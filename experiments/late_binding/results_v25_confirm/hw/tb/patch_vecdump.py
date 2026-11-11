"""v25 Part F2: makes an instrumented COPY of the simulator sources that can dump test vectors (vecdump.inc).

Usage: python3 patch_vecdump.py NOXIM_ROOT DST
  copies NOXIM_ROOT/src and NOXIM_ROOT/bin/Makefile* to DST, links DST/bin/libs to the repository's libraries, and applies
  five edits to the copy. Every edit replaces one exact piece of text that must occur exactly once; otherwise the script
  stops. The repository's sources are not changed. Build: make -C DST/bin MODULE=noxim_vec.
The edits only add calls that write the dump (enabled by the environment variable LB25_VEC); run_vectors.sh checks that
an instrumented run gives a statistics file byte-identical to that of bin/noxim.
"""
import io
import os
import shutil
import sys

NL = chr(10)
TAB = chr(9)


def edit(path, old, new):
    s = io.open(path, encoding='utf-8', newline='').read()
    crlf = (chr(13) + NL) in s
    if crlf:
        s = s.replace(chr(13) + NL, NL)
    if s.count(old) != 1:
        raise SystemExit('%s: anchor found %d times: %r' % (path, s.count(old), old[:60]))
    s = s.replace(old, new)
    io.open(path, 'w', encoding='utf-8', newline='').write(s)


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
    shutil.copy(os.path.join(here, 'vecdump.inc'), os.path.join(dst, 'src', 'vecdump.inc'))
    src = os.path.join(dst, 'src')

    # 1. declarations
    edit(os.path.join(src, 'DeftLateBinding.h'),
         '// ---- statistics ------------------------------------------------------' + NL + 'void writeJson(std::ostream &out);',
         '// ---- v25 F2: vector dump (instrumented copy only) ----' + NL +
         'bool vecOn();' + NL +
         'void vecSel(int kind, Router *router, const std::vector<int> &dirs, const RouteData &rd, const std::vector<double> *cost, int choice);' + NL +
         'void vecFront(const RouteData &rd, int held_o, const int *free6, int result);' + NL + NL +
         '// ---- statistics ------------------------------------------------------' + NL + 'void writeJson(std::ostream &out);')

    # 2. the heuristic's choice (the same single call of pickMin, so the same random numbers)
    f = os.path.join(src, 'DeftLateBinding.cpp')
    edit(f,
         '        return chooseWithHysteresis(dirs, cost, hops);' + NL + '    }' + NL + '    return pickMin(dirs, cost);' + NL + '}' + NL + NL + 'int selectQLearning(',
         '        return chooseWithHysteresis(dirs, cost, hops);' + NL + '    }' + NL +
         '    const int v25_choice = pickMin(dirs, cost);' + NL +
         '    vecSel(g_asking_absent ? 0 : 1, router, dirs, rd, &cost, v25_choice);' + NL +
         '    return v25_choice;' + NL + '}' + NL + NL + 'int selectQLearning(')

    # 3. a stored decision of a hop with one offered output (no selection is evaluated there)
    edit(f,
         '    g_la_stored++;' + NL + '    if (offered.size() == 1)' + NL + '        return offered[0];',
         '    g_la_stored++;' + NL + '    if (offered.size() == 1) {' + NL +
         '        vecSel(0, routerById(nrd.current_id), offered, nrd, 0, offered[0]);' + NL +
         '        return offered[0];' + NL + '    }')

    # 4. the dump code itself, at the end of the translation unit
    s = io.open(f, encoding='utf-8', newline='').read()
    io.open(f, 'w', encoding='utf-8', newline='').write(s + NL + '#include "vecdump.inc"' + NL)

    # 5. the output asked at the buffer front: the original function under a new name, and a wrapper that dumps its result
    edit(os.path.join(src, 'Router.h'),
         '    bool outputFreeForHead(const RouteData & route_data, int o);',
         '    bool outputFreeForHead(const RouteData & route_data, int o);' + NL +
         '    int selectionFunctionV25(const vector <int> &directions, const RouteData & route_data);')
    f = os.path.join(src, 'Router.cpp')
    edit(f, 'int Router::selectionFunction(const vector < int >&directions,', 'int Router::selectionFunctionV25(const vector < int >&directions,')
    s = io.open(f, encoding='utf-8', newline='').read()
    wrapper = [
        '',
        '// v25 F2 (instrumented copy only): the original function is selectionFunctionV25; its result is dumped.',
        'int Router::selectionFunction(const vector < int >&directions, const RouteData & route_data)',
        '{',
        '    const int result = selectionFunctionV25(directions, route_data);',
        '    if (DeftLB::vecOn() && DeftLB::isActive() && local_id >= DeftTopology::ChipletRouterCount) {',
        '        int held_o = -1, held_vc = -1;',
        '        if (!reservation_table.findReservation(route_data.dir_in, route_data.vc_id, &held_o, &held_vc))',
        '            held_o = -1;',
        '        int free6[6];',
        '        for (int o = 0; o < 6; o++)',
        '            free6[o] = (o != DIRECTION_LOCAL && outputFreeForHead(route_data, o)) ? 1 : 0;',
        '        DeftLB::vecFront(route_data, held_o, free6, result);',
        '    }',
        '    return result;',
        '}',
        '']
    io.open(f, 'w', encoding='utf-8', newline='').write(s + NL.join(wrapper))
    print('instrumented copy in', dst)


if __name__ == '__main__':
    main()
