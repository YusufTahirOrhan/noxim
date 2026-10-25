/*
 * DEFT_LB: late-binding Vertical-Link routing for the DeFT 2.5D topology.
 *
 * The head flit carries two candidate masks (one bit per VL id):
 *   exit mask  - VLs of the source chiplet that may still be used to go down,
 *   entry mask - VLs of the destination chiplet that may still be used to go up.
 * A singleton mask means the VL was fixed (at injection or by an earlier hop).
 * At every hop the routing relation offers the minimal, turn-legal moves towards
 * any remaining candidate; after a move the mask is pruned to the candidates
 * that the move kept on a minimal path (monotone pruning).
 *
 * With singleton masks and XY turn models the relation is the DeFT relation.
 * Injection-time policies (direction A) fix the masks when the head flit
 * leaves the processing element. The selection strategies DEFT_HEUR
 * (direction C) and DEFT_QL (direction B) choose among the legal outputs.
 */

#ifndef __NOXIMDEFTLATEBINDING_H__
#define __NOXIMDEFTLATEBINDING_H__

#include <ostream>
#include <string>
#include <vector>

#include "DataStructs.h"

struct Router;

namespace DeftLB {

typedef uint64_t VlMask;    // one bit per VL id (up to 64 VLs)

enum TurnModel { TM_XY = 0, TM_OE = 1 };

enum InjectionPolicy {
    POLICY_LATE = 0,    // keep every functional VL as a candidate
    POLICY_LUT,         // offline DeFT table
    POLICY_RANDOM,      // uniform random functional VL
    POLICY_MINDIST,     // minimal total hop count, random tie break
    POLICY_ORACLE,      // hop count + instantaneous global VL-area occupancy
    // v10 baselines (singleton masks; with XY turn models the relation is DeFT's)
    POLICY_NEAR,        // functional VL nearest to the source (exit) / destination (entry) router, ties: lowest id
    POLICY_RAN,         // uniform functional VL per packet, drawn from a separate RNG stream
    POLICY_MTR          // MTR outbound (exit) / inbound (entry) table (-deft_lb mtr_table PATH)
};

struct Config {
    Config();
    InjectionPolicy exit_policy;
    InjectionPolicy entry_policy;
    int chip_tm;
    int ipos_tm;
    // heuristic (direction C)
    double heur_w;          // weight of downstream occupancy (cycles per flit)
    double heur_busy;       // penalty when the output VC is held by another packet
    int heur_lookahead;     // 0: router-local, 1: plus one-hop lookahead
    // Q-learning (direction B)
    double ql_alpha;        // learning rate
    double ql_eps;          // epsilon-greedy exploration probability
    double ql_hop_cost;     // static estimate in cycles per remaining hop
    double ql_w;            // local occupancy weight used by the learner's decision
    double ql_busy;         // local busy-VC penalty used by the learner's decision
    int ql_key;             // learned residual over the static estimate, kept per
                            // 0: destination router, 1: destination chiplet
    // oracle injection policy (upper bound for direction A)
    double oracle_beta;     // cycles per buffered flit near the VL
};

Config &config();
bool setParam(const std::string &key, const std::string &value,
              std::string *error_message);
std::string policyName(InjectionPolicy policy);
std::string turnModelName(int tm);

bool isActive();            // routing algorithm is DEFT_LB on DEFT_2_5D
bool validateConfiguration(std::string *error_message);

// ---- registry --------------------------------------------------------
void registerRouter(int id, Router *router);
Router *routerById(int id);

// ---- geometry --------------------------------------------------------
int footprintX(int router_id);
int footprintY(int router_id);
int chipletOf(int router_id);      // -1 for interposer routers
int vlAtRouter(int router_id);     // VL with an endpoint at this router, -1 otherwise
int neighborId(int router_id, int out_dir);
int arrivalPort(int out_dir);
int lastMoveFromDirIn(int dir_in); // 0..3, or 4 for none (injected / vertical arrival)
int manhattan(int router_a, int router_b);

// Minimal, turn-legal moves (bit d = direction d) from (x,y) towards (tx,ty).
int movesMask(int tm, int x, int y, int last, int tx, int ty);

// ---- routing relation ------------------------------------------------
void legalMoves(const RouteData &route_data, std::vector<int> *directions);
void nextMasks(int router_id, int dir_in, int out_dir,
               int src_id, int dst_id,
               VlMask exit_mask, VlMask entry_mask,
               VlMask *next_exit_mask, VlMask *next_entry_mask);
// Static remaining-path length of the selection; interposer hops weighted by hop_weight_ipos.
double remainingHops(int router_id, int src_id, int dst_id,
                  VlMask exit_mask, VlMask entry_mask);
double hopsAfterMove(const RouteData &route_data, int out_dir);
RouteData nextRouteData(const RouteData &route_data, int out_dir, int out_vc);
void legalOutputsWithVn(const RouteData &route_data, std::vector<int> *directions);

// ---- injection -------------------------------------------------------
// Sets candidate masks (DEFT_LB only) and the source virtual network of a
// packet whose head flit is about to leave the processing element.
// Optional bounded-deviation entry (-deft_lb entry_bound_mode off|min|lut,
// -deft_lb entry_bound_k K; default off): the entry mask is reduced once to a
// non-empty subset of the functional entry candidates whose shortest
// turn-legal path length is within K of the shortest (min) or of the LUT
// entry's (lut).
void prepareHeadPacket(Packet &packet);

// ---- router hooks ----------------------------------------------------
// Called when the head flit is forwarded from router through out_dir.
// Prunes the masks in *flit, updates Q tables and statistics.
void onHeadForward(Router *router, int dir_in, int out_dir, int out_vc,
                   Flit *flit, double now, double front_cycle);
// Called once when a head flit first reaches the front of an input buffer.
// Completes the Q-learning update of the router that sent it.
void onHeadAtFront(Router *router, int dir_in, const Flit &flit, double now);
void onRouteFailure(int router_id, const Flit &flit);
void onHeadConsumed(const Flit &flit, double now);

// ---- selection strategies --------------------------------------------
int selectHeuristic(Router *router, const std::vector<int> &directions,
                    const RouteData &route_data);
int selectQLearning(Router *router, const std::vector<int> &directions,
                    const RouteData &route_data);
bool qLearningEnabled();

// ---- RC baseline (-deft_lb rc 1; off by default) ---------------------
// Outbound injection permission: true when the packet (head not yet sent)
// may leave its PE; requests a slot of the exit boundary router's RC buffer.
bool rcEnabled();
int rcSlots();
bool rcMayInject(const Packet &packet, double now);
// The tail of an outbound packet left the RC buffer of this boundary router.
void rcRelease(int boundary_router_id, double now);

// ---- plain DEFT VL usage counter (-deft_lb count_vl 1; off by default) ---
bool countPlainVl();
void onPlainHubForward(int router_id);

// ---- statistics ------------------------------------------------------
void writeJson(std::ostream &out);

} // namespace DeftLB

#endif
