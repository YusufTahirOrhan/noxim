#include "Routing_INTERPOSER_AWARE_XY.h"

#include "../DeftTopology.h"
#include "../GlobalParams.h"
#include "../Logger.h"

RoutingAlgorithmsRegister
    Routing_INTERPOSER_AWARE_XY::routingAlgorithmsRegister(
        ROUTING_INTERPOSER_AWARE_XY,
        getInstance());

Routing_INTERPOSER_AWARE_XY *
    Routing_INTERPOSER_AWARE_XY::routing_INTERPOSER_AWARE_XY = 0;

namespace {

struct RoutePlan {
    DeftTopology::VerticalLinkInfo source_exit;
    DeftTopology::VerticalLinkInfo destination_entry;
};

int absoluteDifference(int a, int b)
{
    return a > b ? a - b : b - a;
}

int footprintDistance(const DeftTopology::RouterInfo &a,
                      const DeftTopology::RouterInfo &b)
{
    return absoluteDifference(a.footprint_x, b.footprint_x) +
           absoluteDifference(a.footprint_y, b.footprint_y);
}

void pushXyDirection(const DeftTopology::RouterInfo &current,
                     const DeftTopology::RouterInfo &target,
                     vector<int> *directions)
{
    if (target.footprint_x > current.footprint_x)
        directions->push_back(DIRECTION_EAST);
    else if (target.footprint_x < current.footprint_x)
        directions->push_back(DIRECTION_WEST);
    else if (target.footprint_y > current.footprint_y)
        directions->push_back(DIRECTION_SOUTH);
    else if (target.footprint_y < current.footprint_y)
        directions->push_back(DIRECTION_NORTH);
}

bool sameChiplet(const DeftTopology::RouterInfo &a,
                 const DeftTopology::RouterInfo &b)
{
    return a.layer == DeftTopology::ROUTER_LAYER_CHIPLET &&
           b.layer == DeftTopology::ROUTER_LAYER_CHIPLET &&
           a.chiplet_id == b.chiplet_id;
}

void logVerticalLinkTraversal(const char *phase,
                              const RouteData &route_data,
                              const DeftTopology::VerticalLinkInfo &link)
{
    noxim::Logger::instance()
        .message(noxim::LOG_LEVEL_DEBUG_VALUE,
                 __FILE__,
                 __func__,
                 "IA-XY")
        << "IA-XY " << phase
        << " src=" << route_data.src_id
        << " dst=" << route_data.dst_id
        << " current=" << route_data.current_id
        << " vl_id=" << link.vl_id
        << " boundary=" << link.chiplet_endpoint_router_id
        << " interposer=" << link.interposer_endpoint_router_id
        << endl;
}

bool preferPlan(int candidate_cost,
                const DeftTopology::VerticalLinkInfo &candidate_source_exit,
                const DeftTopology::VerticalLinkInfo &candidate_destination_entry,
                bool has_best,
                int best_cost,
                const RoutePlan &best_plan)
{
    if (!has_best)
        return true;

    if (candidate_cost != best_cost)
        return candidate_cost < best_cost;

    if (candidate_source_exit.vl_id != best_plan.source_exit.vl_id)
        return candidate_source_exit.vl_id < best_plan.source_exit.vl_id;

    return candidate_destination_entry.vl_id <
           best_plan.destination_entry.vl_id;
}

bool selectRoutePlan(const DeftTopology::RouterInfo &source,
                     const DeftTopology::RouterInfo &destination,
                     RoutePlan *route_plan)
{
    const vector<DeftTopology::VerticalLinkInfo> source_links =
        DeftTopology::functionalVerticalLinksForChiplet(source.chiplet_id);
    const vector<DeftTopology::VerticalLinkInfo> destination_links =
        DeftTopology::functionalVerticalLinksForChiplet(
            destination.chiplet_id);

    bool has_best = false;
    int best_cost = 0;
    RoutePlan best_plan;

    for (vector<DeftTopology::VerticalLinkInfo>::const_iterator source_link =
             source_links.begin();
         source_link != source_links.end();
         ++source_link) {
        DeftTopology::RouterInfo source_boundary =
            DeftTopology::decodeRouterId(
                source_link->chiplet_endpoint_router_id);
        DeftTopology::RouterInfo source_interposer =
            DeftTopology::decodeRouterId(
                source_link->interposer_endpoint_router_id);

        for (vector<DeftTopology::VerticalLinkInfo>::const_iterator
                 destination_link = destination_links.begin();
             destination_link != destination_links.end();
             ++destination_link) {
            DeftTopology::RouterInfo destination_interposer =
                DeftTopology::decodeRouterId(
                    destination_link->interposer_endpoint_router_id);
            DeftTopology::RouterInfo destination_boundary =
                DeftTopology::decodeRouterId(
                    destination_link->chiplet_endpoint_router_id);

            const int candidate_cost =
                footprintDistance(source, source_boundary) +
                footprintDistance(source_interposer,
                                  destination_interposer) +
                footprintDistance(destination_boundary, destination);

            if (preferPlan(candidate_cost,
                           *source_link,
                           *destination_link,
                           has_best,
                           best_cost,
                           best_plan)) {
                best_plan.source_exit = *source_link;
                best_plan.destination_entry = *destination_link;
                best_cost = candidate_cost;
                has_best = true;
            }
        }
    }

    if (!has_best)
        return false;

    if (route_plan != 0)
        *route_plan = best_plan;
    return true;
}

} // namespace

Routing_INTERPOSER_AWARE_XY * Routing_INTERPOSER_AWARE_XY::getInstance()
{
    if (routing_INTERPOSER_AWARE_XY == 0)
        routing_INTERPOSER_AWARE_XY =
            new Routing_INTERPOSER_AWARE_XY();

    return routing_INTERPOSER_AWARE_XY;
}

vector<int> Routing_INTERPOSER_AWARE_XY::route(Router * router,
                                               const RouteData & routeData)
{
    (void)router;

    vector<int> directions;

    if (GlobalParams::topology != TOPOLOGY_DEFT_2_5D)
        return directions;

    DeftTopology::RouterInfo current =
        DeftTopology::decodeRouterId(routeData.current_id);
    DeftTopology::RouterInfo source =
        DeftTopology::decodeRouterId(routeData.src_id);
    DeftTopology::RouterInfo destination =
        DeftTopology::decodeRouterId(routeData.dst_id);

    if (current.layer == DeftTopology::ROUTER_LAYER_INVALID ||
        source.layer != DeftTopology::ROUTER_LAYER_CHIPLET ||
        destination.layer != DeftTopology::ROUTER_LAYER_CHIPLET)
        return directions;

    if (sameChiplet(source, destination)) {
        if (current.layer == DeftTopology::ROUTER_LAYER_CHIPLET &&
            current.chiplet_id == destination.chiplet_id)
            pushXyDirection(current, destination, &directions);
        return directions;
    }

    RoutePlan route_plan;
    if (!selectRoutePlan(source, destination, &route_plan))
        return directions;

    if (current.layer == DeftTopology::ROUTER_LAYER_CHIPLET) {
        if (current.chiplet_id == source.chiplet_id) {
            if (routeData.current_id ==
                route_plan.source_exit.chiplet_endpoint_router_id) {
                if (route_plan.source_exit.is_functional) {
                    logVerticalLinkTraversal("source_exit",
                                             routeData,
                                             route_plan.source_exit);
                    directions.push_back(DIRECTION_HUB);
                }
                return directions;
            }

            DeftTopology::RouterInfo source_boundary =
                DeftTopology::decodeRouterId(
                    route_plan.source_exit.chiplet_endpoint_router_id);
            pushXyDirection(current, source_boundary, &directions);
            return directions;
        }

        if (current.chiplet_id == destination.chiplet_id) {
            pushXyDirection(current, destination, &directions);
            return directions;
        }

        return directions;
    }

    if (current.layer == DeftTopology::ROUTER_LAYER_INTERPOSER) {
        if (routeData.current_id ==
            route_plan.destination_entry.interposer_endpoint_router_id) {
            if (route_plan.destination_entry.is_functional) {
                logVerticalLinkTraversal("destination_entry",
                                         routeData,
                                         route_plan.destination_entry);
                directions.push_back(DIRECTION_HUB);
            }
            return directions;
        }

        DeftTopology::RouterInfo destination_interposer =
            DeftTopology::decodeRouterId(
                route_plan.destination_entry.interposer_endpoint_router_id);
        pushXyDirection(current, destination_interposer, &directions);
    }

    return directions;
}
