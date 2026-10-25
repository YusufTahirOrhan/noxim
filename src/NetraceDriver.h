/*
 * Netrace-driven traffic (v13 Part E; -netrace FILE, off by default).
 *
 * FILE is a packet list cut from a Netrace trace by experiments/late_binding/netrace/netrace_cut
 * (one packet per line: cycle id type src dst node_types num_deps dep...). Trace node n is chiplet
 * router n (the 64 nodes of the 8x8 trace map onto the 2x2 DEFT_2_5D footprint, chiplet (x/4, y/4)).
 *
 * Every packet of the window (cycle < region start + -netrace_window) is injected exactly once:
 *   - at its trace cycle (simulation cycle + region start) if all packets it depends on are delivered,
 *   - otherwise 8 cycles (Netrace's L2_LATENCY) after the last of them is delivered (-netrace_deps 1),
 *   - at most one new packet per node and cycle (as in Netrace's example simulator).
 * With -netrace_deps 0 packets are replayed by their trace cycle only. Packet sizes: Netrace's byte
 * sizes / (flit_size / 8), at least 2 flits. A packet with source = destination is counted as
 * delivered at once. The simulation ends when every packet of the window has been delivered.
 */

#ifndef __NOXIMNETRACEDRIVER_H__
#define __NOXIMNETRACEDRIVER_H__

#include <ostream>

namespace NetraceDriver {

bool active();
// Called by every PE once per cycle (the first call of a cycle advances the driver).
// Returns true and fills dst/size/trace_id when a packet of this node may leave now.
bool popReady(int node, double now, int *dst, int *size, int *trace_id);
// The tail flit of packet trace_id reached its destination.
void onDelivered(int trace_id, double now);
// All packets of the window have been injected and delivered.
bool finished();
long completionCycle();
void writeJsonFields(std::ostream &out);

} // namespace NetraceDriver

#endif
