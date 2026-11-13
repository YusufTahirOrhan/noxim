"""v26 A3: makes an instrumented COPY of the simulator sources that dumps every hop of a head flit (hopdump.inc).

Usage: python3 patch_hopdump.py NOXIM_ROOT DST
  copies NOXIM_ROOT/src and NOXIM_ROOT/bin/Makefile* to DST, links DST/bin/libs to the repository's libraries, and applies
  four edits to the copy. Every edit matches one piece of text that must occur exactly once; otherwise the script stops. The
  repository's sources are not changed. Build: make -C DST/bin MODULE=noxim_hop.
The edits only add calls that write the dump (enabled by the environment variable LB26_HOP); experiments_v26_conf.py checks
that every instrumented run gives a statistics file byte-identical to that of bin/noxim.
The mechanism is the one of round 25 (results_v25_confirm/hw/tb/patch_vecdump.py).
"""
import io
import os
import re
import shutil
import sys

NL = chr(10)


def read(path):
    return io.open(path, encoding='utf-8', newline='').read().replace(chr(13) + NL, NL)


def write(path, s):
    io.open(path, 'w', encoding='utf-8', newline='').write(s)


def edit(path, old, new):
    s = read(path)
    if s.count(old) != 1:
        raise SystemExit('%s: anchor found %d times: %r' % (path, s.count(old), old[:60]))
    write(path, s.replace(old, new))


def edit_re(path, pattern, repl):
    s = read(path)
    found = re.findall(pattern, s)
    if len(found) != 1:
        raise SystemExit('%s: pattern found %d times: %r' % (path, len(found), pattern[:60]))
    write(path, re.sub(pattern, repl, s, count=1))


def main():
    root, dst = sys.argv[1], sys.argv[2]
    here = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(os.path.join(dst, 'bin'))
    shutil.copytree(os.path.join(root, 'src'), os.path.join(dst, 'src'))
    for f in ('Makefile', 'Makefile.deps'):
        shutil.copy(os.path.join(root, 'bin', f), os.path.join(dst, 'bin', f))
    os.symlink(os.path.join(root, 'bin', 'libs'), os.path.join(dst, 'bin', 'libs'))
    shutil.copy(os.path.join(here, 'hopdump.inc'), os.path.join(dst, 'src', 'hopdump.inc'))
    src = os.path.join(dst, 'src')

    # 1. declarations
    edit(os.path.join(src, 'DeftLateBinding.h'),
         '// ---- statistics ------------------------------------------------------' + NL + 'void writeJson(std::ostream &out);',
         '// ---- v26 A3: hop dump (instrumented copy only) ----' + NL +
         'bool hopOn();' + NL +
         'void hopBefore(const Flit &flit);' + NL +
         'void hopAfter(Router *router, int dir_in, int out_dir, int out_vc, const Flit &after);' + NL + NL +
         '// ---- statistics ------------------------------------------------------' + NL + 'void writeJson(std::ostream &out);')

    # 2. the dump code itself, at the end of the translation unit
    f = os.path.join(src, 'DeftLateBinding.cpp')
    write(f, read(f) + NL + '#include "hopdump.inc"' + NL)

    # 3. the head before the forward hook prunes its masks (Router::txProcess, forwarding phase)
    f = os.path.join(src, 'Router.cpp')
    edit_re(f, r'(if \(flit\.flit_type == FLIT_TYPE_HEAD && DeftLB::isActive\(\)\)\s+DeftLB::onHeadForward\(this, i, o, output_vc, &flit,)',
            'if (flit.flit_type == FLIT_TYPE_HEAD)' + NL + '    DeftLB::hopBefore(flit);' + NL + r'\1')

    # 4. the hop record, after the forward hook and before the output VC is written into the flit
    edit_re(f, r'(if \(flit\.flit_type == FLIT_TYPE_HEAD && o == DIRECTION_HUB && DeftLB::countPlainVl\(\)\))',
            'if (flit.flit_type == FLIT_TYPE_HEAD)' + NL + '    DeftLB::hopAfter(this, i, o, output_vc, flit);' + NL + r'\1')
    print('instrumented copy in', dst)


if __name__ == '__main__':
    main()
