"""Apply the review-v22 experiment patches to a COPY of the Noxim sources (never to the repository).

Adds three options, all off by default, so the unpatched behaviour is unchanged:
  -deft_lb up_keep 1      the Up vertical link keeps the packet's VN; the switch to VN1 happens at the destination
                          chiplet's boundary router (the paper's Algorithm 1: "coming from the interposer -> VN.1" is
                          executed by the chiplet boundary router; CEA's Routing_DEFT does the same)
  -deft_lb rr_fallback 1  at a round-robin VN reassignment, when the counter's VC is busy, take the other VC if free
  -deft_lb pipe_all N     every head flit of every routing algorithm waits N cycles after reaching an input-buffer
                          front before it may reserve an output (a crude uniform router pipeline for all methods)
Usage: python3 patch_review.py SRC_DIR
"""
import sys
import os

src = sys.argv[1]


def patch(path, old, new, count=1):
    p = os.path.join(src, path)
    s = open(p, encoding='utf-8').read()
    assert s.count(old) == count, (path, old[:60], s.count(old))
    s = s.replace(old, new)
    open(p, 'w', encoding='utf-8', newline='\n').write(s)
    print('patched', path)


# ---- DeftVirtualNetwork.h ----
patch('DeftVirtualNetwork.h',
      'void setRoundRobinActive(bool active);\nbool roundRobinActive();\n',
      'void setRoundRobinActive(bool active);\nbool roundRobinActive();\n'
      '// review v22 experiment options (off by default)\n'
      'void setUpKeep(bool active);\nbool upKeep();\n'
      'void setRrFallback(bool active);\nbool rrFallback();\n')

# ---- DeftVirtualNetwork.cpp ----
patch('DeftVirtualNetwork.cpp',
      'bool vn_rr_active = false;\n',
      'bool vn_rr_active = false;\n'
      '// review v22: Up link keeps the VN (switch at the destination boundary router); RR fallback to the free VC\n'
      'bool vn_up_keep = false;\nbool vn_rr_fallback = false;\n')
patch('DeftVirtualNetwork.cpp',
      'bool roundRobinActive()\n{\n    return vn_rr_active;\n}\n',
      'bool roundRobinActive()\n{\n    return vn_rr_active;\n}\n\n'
      'void setUpKeep(bool active)\n{\n    vn_up_keep = active;\n}\n\n'
      'bool upKeep()\n{\n    return vn_up_keep;\n}\n\n'
      'void setRrFallback(bool active)\n{\n    vn_rr_fallback = active;\n}\n\n'
      'bool rrFallback()\n{\n    return vn_rr_fallback;\n}\n')
patch('DeftVirtualNetwork.cpp',
      '    else if (isInterposerToChiplet(route_data, output_direction) ||\n'
      '             isFromInterposerInsideChiplet(route_data))\n'
      '    {\n        output_vn = VN1;\n    }\n',
      '    else if (isFromInterposerInsideChiplet(route_data))\n'
      '    {\n        output_vn = VN1;\n    }\n'
      '    else if (isInterposerToChiplet(route_data, output_direction))\n'
      '    {\n        // review v22: with up_keep the Up link keeps the input VN (paper / CEA); default: VN1\n'
      '        output_vn = vn_up_keep ? input_vn : VN1;\n    }\n')

# ---- DeftLateBinding.h / .cpp: pipe_all ----
patch('DeftLateBinding.h',
      'int decisionDelay();\n',
      'int decisionDelay();\n'
      '// review v22: uniform per-hop head delay for every routing algorithm (-deft_lb pipe_all N; 0 by default)\n'
      'int pipeAll();\n')
patch('DeftLateBinding.cpp',
      'int g_decision_delay = 0;\n',
      'int g_decision_delay = 0;\nint g_pipe_all = 0;   // review v22\n')
patch('DeftLateBinding.cpp',
      '    else if (key == "hop_stats") {\n',
      '    else if (key == "pipe_all") {\n'
      '        if (d < 0 || d != std::floor(d)) {\n'
      '            if (error_message) *error_message = "pipe_all must be an integer >= 0";\n'
      '            return false;\n'
      '        }\n'
      '        g_pipe_all = (int) d;\n'
      '    }\n'
      '    else if (key == "up_keep") {\n'
      '        DeftVirtualNetwork::setUpKeep(d != 0.0);\n'
      '    }\n'
      '    else if (key == "rr_fallback") {\n'
      '        DeftVirtualNetwork::setRrFallback(d != 0.0);\n'
      '    }\n'
      '    else if (key == "hop_stats") {\n')
patch('DeftLateBinding.cpp',
      'int decisionDelay()\n{\n    return g_decision_delay;\n}\n',
      'int decisionDelay()\n{\n    return g_decision_delay;\n}\n\nint pipeAll()\n{\n    return g_pipe_all;\n}\n')

# ---- Router.cpp: pipe_all wait and RR fallback ----
# The decision delay counts from the end of the pipe_all wait, so a multi-output hop of a late-binding router costs
# pipe_all + decision_delay cycles (its decision needs N cycles more than the baseline's route stage), a single-output hop
# pipe_all. With pipe_all = 0 this is the original behaviour.
patch('Router.cpp',
      '\t\t\t  DeftLB::mustWaitDecision(route_data, deft_front_cycle[i][vc],\n',
      '\t\t\t  DeftLB::mustWaitDecision(route_data, deft_front_cycle[i][vc] + DeftLB::pipeAll(),\n')
patch('Router.cpp',
      '\t\t      // -deft_lb decision_delay N (off by default): N extra cycles where more than one output is offered\n',
      '\t\t      // review v22: -deft_lb pipe_all N, every head of every algorithm waits N cycles at the buffer front\n'
      '\t\t      if (DeftLB::pipeAll() > 0 &&\n'
      '\t\t\t  sc_time_stamp().to_double() / GlobalParams::clock_period_ps < deft_front_cycle[i][vc] + DeftLB::pipeAll())\n'
      '\t\t\t  continue;\n\n'
      '\t\t      // -deft_lb decision_delay N (off by default): N extra cycles where more than one output is offered\n')
patch('Router.cpp',
      '\t\t      int rt_status = reservation_table.checkReservation(r,o);\n',
      '\t\t      int rt_status = reservation_table.checkReservation(r,o);\n'
      '\t\t      // review v22: -deft_lb rr_fallback 1, take the other VC of a round-robin reassignment when the\n'
      '\t\t      // counter\'s VC is held and the other one is free\n'
      '\t\t      if (rt_status == RT_OUTVC_BUSY && uses_deft_round_robin_reassignment &&\n'
      '\t\t\t  DeftVirtualNetwork::rrFallback())\n'
      '\t\t      {\n'
      '\t\t\t  TReservation r2 = r;\n'
      '\t\t\t  r2.output_vc = 1 - r.output_vc;\n'
      '\t\t\t  if (reservation_table.checkReservation(r2, o) == RT_AVAILABLE)\n'
      '\t\t\t  {\n'
      '\t\t\t      r = r2;\n'
      '\t\t\t      rt_status = RT_AVAILABLE;\n'
      '\t\t\t  }\n'
      '\t\t      }\n')
print('all patches applied')
