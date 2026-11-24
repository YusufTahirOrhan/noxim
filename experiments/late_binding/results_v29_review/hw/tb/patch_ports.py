"""v29 Part E4: adds the port counters (portcount.inc) to an instrumented COPY of the simulator sources.

Usage: python3 patch_ports.py DST
  DST is the copy that results_v25_confirm/hw/tb/patch_vecdump.py made (DST/src). Four edits to the copy; each replaces one
  exact piece of text that must occur exactly once, otherwise the script stops. The repository's sources are not changed.
The edits only add calls that count (enabled by the environment variable LB29_PORTS); experiments_v29_hw2.py checks that an
instrumented run gives a statistics file byte-identical to that of bin/noxim.
"""
import io
import os
import shutil
import sys

NL = chr(10)


def edit(path, old, new):
    s = io.open(path, encoding='utf-8', newline='').read()
    if (chr(13) + NL) in s:
        s = s.replace(chr(13) + NL, NL)
    if s.count(old) != 1:
        raise SystemExit('%s: anchor found %d times: %r' % (path, s.count(old), old[:60]))
    io.open(path, 'w', encoding='utf-8', newline='').write(s.replace(old, new))


def main():
    dst = sys.argv[1]
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(dst, 'src')
    shutil.copy(os.path.join(here, 'portcount.inc'), os.path.join(src, 'portcount.inc'))

    # 1. declarations
    edit(os.path.join(src, 'DeftLateBinding.h'),
         'void writeJson(std::ostream &out);',
         '// ---- v29 E4: flits per input port (instrumented copy only) ----' + NL +
         'bool portsOn();' + NL +
         'void portFlit(int router, int port, int vc, bool head);' + NL +
         'void portFill(int router, int port, int vc, int fill);' + NL + NL +
         'void writeJson(std::ostream &out);')

    # 2. a flit is stored in an input buffer
    f = os.path.join(src, 'Router.cpp')
    a = 'LOG << " Flit " << received_flit << " collected from Input[" << i << "][" << vc <<"]" << endl;'
    edit(f, a, 'if (DeftLB::portsOn()) DeftLB::portFlit(local_id, i, vc, received_flit.flit_type == FLIT_TYPE_HEAD); ' + a)

    # 3. once per cycle and input port: the fill of its buffers
    a = 'ack_rx[i].write(current_level_rx[i]);'
    edit(f, a, 'if (DeftLB::portsOn()) for (int pv = 0; pv < GlobalParams::n_virtual_channels && pv < 2; pv++) ' +
         'DeftLB::portFill(local_id, i, pv, (int) buffer[i][pv].Size()); ' + a)

    # 4. the counting code itself, at the end of the translation unit
    f = os.path.join(src, 'DeftLateBinding.cpp')
    s = io.open(f, encoding='utf-8', newline='').read()
    io.open(f, 'w', encoding='utf-8', newline='').write(s + NL + '#include "portcount.inc"' + NL)
    print('port counters added to', dst)


if __name__ == '__main__':
    main()
