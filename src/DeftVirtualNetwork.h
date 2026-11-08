/*
 * DeFT virtual-network assignment helpers.
 */

#ifndef __NOXIMDEFTVIRTUALNETWORK_H__
#define __NOXIMDEFTVIRTUALNETWORK_H__

#include "DataStructs.h"

namespace DeftVirtualNetwork {

enum {
    VN0 = 0,
    VN1 = 1,
    VirtualNetworkCount = 2
};

bool isEnabled();
// DeFT VN rules on (default) or off (MTR, RC baselines: the packet keeps the VC drawn at injection).
void setRulesActive(bool active);
bool rulesActive();
// -deft_vn_rr 1 (off by default): DeFT's Algorithm 1 at the boundary router. A VN0 packet going Horizontal -> Down is
// reassigned to VN0 or VN1 by round-robin, R3 applies to the input VN, and the source and boundary round-robin counters are
// per router instead of global.
void setRoundRobinActive(bool active);
bool roundRobinActive();
// -deft_up_keep 1 (off by default; v23, review R1): the Up VL keeps the packet's VN and the switch to VN1 happens at the
// destination chiplet's boundary router before any Up -> Horizontal move (DeFT paper, Algorithm 1 and Theorem III.4).
void setUpKeep(bool active);
bool upKeep();
// -deft_rr_fallback 1 (off by default; v23, review R2): a round-robin VN whose VC is held (boundary) or whose local buffer is
// full (source) is replaced by the other VC when that one is free; the counter advances on every successful assignment.
void setRrFallback(bool active);
bool rrFallback();
bool isValidVirtualNetwork(int vc_id);
bool canTransition(int from_vn, int to_vn);
bool isOutputDirectionAllowed(const RouteData &route_data,
                              int output_direction);

// exit_mask: DEFT_LB candidate exit VLs of the packet (0 = not DEFT_LB).
// A boundary-router source may start in VN1 only if the packet is committed
// to the source's own VL (Finding F1 of the research notebook).
// local_vc_full (optional): the router's local input buffers that are full, per VC; used by the source fallback.
int assignSourceVirtualNetwork(int src_id, int dst_id, uint64_t exit_mask = 0, const bool *local_vc_full = 0);
int selectOutputVirtualNetwork(const RouteData &route_data,
                               int output_direction,
                               bool *uses_round_robin_reassignment);
void commitBoundaryReassignmentRoundRobin(int router_id);

} // namespace DeftVirtualNetwork

#endif
