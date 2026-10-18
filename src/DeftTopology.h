/*
 * DeFT 2.5D topology mapping helpers.
 */

#ifndef __NOXIMDEFTTOPOLOGY_H__
#define __NOXIMDEFTTOPOLOGY_H__

#include <string>
#include <vector>

namespace DeftTopology {

// Instance size, set at run time by configure() (parameters deft_chiplets_x,
// deft_chiplets_y, deft_chiplet_w, deft_chiplet_h; defaults 2, 2, 4, 4: four
// 4x4 chiplets on an 8x8 interposer). The values below are derived and must
// only be changed through configure().
extern int ChipletGridWidth;
extern int ChipletGridHeight;
extern int ChipletCount;
extern int ChipletLocalWidth;
extern int ChipletLocalHeight;
extern int FootprintWidth;
extern int FootprintHeight;
extern int ChipletRouterCount;
extern int InterposerRouterCount;
extern int TotalRouters;
static const int VerticalLinksPerChiplet = 4;
static const int MaxVerticalLinkCount = 64;     // VL masks are 64-bit
extern int VerticalLinkCount;
extern int LayoutWidth;
extern int LayoutHeight;

// Sets the instance size and rebuilds the VL model. Returns false (and an
// error message) for an unsupported size: chiplet grid >= 1x1 with at least
// 2 chiplets, chiplets of at least 3x3 routers, at most 64 VLs.
bool configure(int chiplets_x, int chiplets_y, int chiplet_w, int chiplet_h,
               std::string *error_message = 0);
// Chiplet-local slot positions (N, E, S, W) as functions of the chiplet size:
// N = (1, 0), E = (w - 1, 1), S = (w - 2, h - 1), W = (0, h - 2); for 4x4 this is
// N = (1, 0), E = (3, 1), S = (2, 3), W = (0, 2) as in the fixed instance.
int slotLocalX(int slot);
int slotLocalY(int slot);

enum RouterLayer {
    ROUTER_LAYER_INVALID = -1,
    ROUTER_LAYER_CHIPLET = 0,
    ROUTER_LAYER_INTERPOSER = 1
};

enum VerticalLinkSlot {
    VL_SLOT_NORTH = 0,
    VL_SLOT_EAST = 1,
    VL_SLOT_SOUTH = 2,
    VL_SLOT_WEST = 3
};

struct RouterInfo {
    int id;
    RouterLayer layer;
    int footprint_x;
    int footprint_y;
    int chiplet_id;
    int local_x;
    int local_y;
    bool boundary_router;
    int vertical_link_id;
};

struct VerticalLinkInfo {
    int vl_id;
    int owner_chiplet_id;
    VerticalLinkSlot slot;
    int chiplet_endpoint_router_id;
    int interposer_endpoint_router_id;
    int footprint_x;
    int footprint_y;
    bool is_functional;
};

struct BoundaryRouterInfo {
    int router_id;
    int owner_chiplet_id;
    int local_x;
    int local_y;
    VerticalLinkSlot slot;
    int vertical_link_id;
    int interposer_endpoint_router_id;
};

bool isChipletRouter(int id);
bool isInterposerRouter(int id);
RouterInfo decodeRouterId(int id);
int chipletRouterId(int chiplet_id, int local_x, int local_y);
int interposerRouterId(int footprint_x, int footprint_y);
bool isBoundaryRouter(int id);
std::vector<BoundaryRouterInfo> boundaryRouters();
std::vector<BoundaryRouterInfo> boundaryRoutersForChiplet(int chiplet_id);
bool boundaryRouterById(int router_id, BoundaryRouterInfo *boundary_router);
bool boundaryRouterForVerticalLink(int vl_id, BoundaryRouterInfo *boundary_router);
bool validateBoundaryRouterModel(std::string *error_message = 0);
const std::vector<VerticalLinkInfo> &verticalLinks();
std::vector<VerticalLinkInfo> verticalLinksForChiplet(int chiplet_id);
std::vector<VerticalLinkInfo> functionalVerticalLinksForChiplet(int chiplet_id);
const VerticalLinkInfo *verticalLinkById(int vl_id);
const VerticalLinkInfo *verticalLinkForBoundaryRouter(int id);
const VerticalLinkInfo *verticalLinkForInterposerRouter(int id);
const VerticalLinkInfo *verticalLinkBetweenRouters(int router_a_id, int router_b_id);
bool isVerticalLinkFunctional(int vl_id);
bool setVerticalLinkFunctional(int vl_id, bool is_functional);
void resetVerticalLinkStates();
bool hasFunctionalVerticalLinkForChiplet(int chiplet_id);
bool validateVerticalLinkModel(std::string *error_message = 0);
int chipletEndpointForVerticalLink(int vl_id);
int interposerEndpointForVerticalLink(int vl_id);
std::string layerName(RouterLayer layer);
std::string slotName(VerticalLinkSlot slot);

} // namespace DeftTopology

#endif
