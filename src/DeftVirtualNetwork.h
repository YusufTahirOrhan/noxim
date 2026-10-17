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
bool isValidVirtualNetwork(int vc_id);
bool canTransition(int from_vn, int to_vn);
bool isOutputDirectionAllowed(const RouteData &route_data,
                              int output_direction);

// exit_mask: DEFT_LB candidate exit VLs of the packet (0 = not DEFT_LB).
// A boundary-router source may start in VN1 only if the packet is committed
// to the source's own VL (Finding F1 of the research notebook).
int assignSourceVirtualNetwork(int src_id, int dst_id, int exit_mask = 0);
int selectOutputVirtualNetwork(const RouteData &route_data,
                               int output_direction,
                               bool *uses_round_robin_reassignment);
void commitBoundaryReassignmentRoundRobin();

} // namespace DeftVirtualNetwork

#endif
