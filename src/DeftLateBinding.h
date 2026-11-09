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

// TM_YX (v24): dimension order with Y first. TM_O1 (v24, interposer only): the order follows the packet's virtual network,
// XY in VN0 and YX in VN1 (the VN does not change on the interposer, so each VN's interposer channels carry one order).
enum TurnModel { TM_XY = 0, TM_OE = 1, TM_YX = 2, TM_O1 = 3 };

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
// vn: the packet's virtual network at router_id (its input VC); it selects the interposer order with ipos_tm O1.
void nextMasks(int router_id, int dir_in, int out_dir,
               int src_id, int dst_id,
               VlMask exit_mask, VlMask entry_mask,
               VlMask *next_exit_mask, VlMask *next_entry_mask, int vn = 0);
// Static remaining-path length of the selection; interposer hops weighted by hop_weight_ipos.
double remainingHops(int router_id, int src_id, int dst_id,
                  VlMask exit_mask, VlMask entry_mask);
double hopsAfterMove(const RouteData &route_data, int out_dir);
RouteData nextRouteData(const RouteData &route_data, int out_dir, int out_vc);
void legalOutputsWithVn(const RouteData &route_data, std::vector<int> *directions);

// ---- decision delay (-deft_lb decision_delay N; 0 by default) -----------
// A head at a router that offers it more than one output waits N extra cycles from reaching the buffer front
// before it may reserve an output. Hops with one offered output are not delayed.
int decisionDelay();
bool mustWaitDecision(const RouteData &route_data, double front_cycle, double now);

// ---- injection -------------------------------------------------------
// Sets candidate masks (DEFT_LB only) and the source virtual network of a
// packet whose head flit is about to leave the processing element.
// Optional bounded-deviation entry (-deft_lb entry_bound_mode off|min|lut,
// -deft_lb entry_bound_k K; default off): the entry mask is reduced once to a
// non-empty subset of the functional entry candidates whose shortest
// turn-legal path length is within K of the shortest (min) or of the LUT
// entry's (lut).
// local_vc_full (optional, v23): which local input-buffer VCs of the source router are full (for -deft_rr_fallback).
void prepareHeadPacket(Packet &packet, const bool *local_vc_full = 0);

// ---- v23 B2: lookahead routing (-deft_lb lookahead_route 1; off by default) -------
// The router that forwards a head computes the next router's decision from that router's state at this moment
// (candidate masks after the move, arrival port, destination, occupancies, lookahead value, residuals) and stores it in
// the head. The next router uses the stored output if it is among its offered outputs (it must be).
bool lookaheadRoute();
int precomputeNextDecision(const RouteData &next_route_data);
void onStoredDecisionUsed(int stored, int fresh, bool multi = false);
// v24 B2 (-deft_lb lookahead_fallback 1; off by default): a head with a stored decision that holds no output yet asks, every
// cycle, for the stored output if it is free, else for the first other offered output that is free, else for the stored one
// (Router::selectionFunction). blocked: the stored output was not free; other: another output was requested.
bool lookaheadFallback();
void onFallbackCheck(bool blocked, bool other);
// The input buffer that output out_dir of router_id feeds, VC out_vc, is full: the neighbour's buffer read directly, as the
// selection's occupancy term reads it.
bool downstreamVcFull(int router_id, int out_dir, int out_vc);

// ---- v23 B4: herding guard (-deft_lb hysteresis D; 0 by default) ----------------------
// The selection leaves the default output (smallest remaining hop count, first in the offer order on ties) only if
// cost(best) < cost(default) - D.
double hysteresis();

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
// DEFT_FAST (v21): a selection meant to decide within one cycle. Off unless -sel DEFT_FAST.
// cost(o) = w f(o) + beta b(o) + H(o) + L(o) [+ R(o, chiplet(d)) with -deft_lb fast_ql 1], with w = heur_w and beta = heur_busy.
// f, b: registered in the previous cycle. L(o): the minimum of w f + beta b over the outputs of the router behind o, registered
// there and sent over the link, so one cycle older. H(o): from a ROM, equal to hopsAfterMove (results_v21_fastsel/tb/rom_check.cpp).
int selectFast(Router *router, const std::vector<int> &directions,
               const RouteData &route_data);
bool fastActive();
void fastTick(double now);     // once per cycle, before any router changes state; only called when fastActive()
double fastHops(const RouteData &route_data, int out_dir);
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

// ---- VC usage statistics (-deft_lb vc_stats FILE; off by default) -------
// Observation only: nothing here feeds back into routing, selection or flow control and no
// random number is drawn. Works for every routing on DEFT_2_5D (plain DEFT included).
bool vcStatsOn();
// A flit left through output out_dir on VC out_vc. Call with the flit as sent.
void vcStatsForward(int router_id, int out_dir, int out_vc, const Flit &flit, double now);
// A head flit waited this cycle for (out_dir, out_vc): held = VC held by another packet,
// otherwise no credit (downstream VC buffer full).
void vcStatsWait(int router_id, int out_dir, int out_vc, bool held, double now);
void vcStatsSample(Router *router, double now);             // input-buffer occupancy, once per cycle
void vcStatsRcSample(int router_id, int flits, int slots, double now);  // RC buffer, once per cycle

// ---- statistics ------------------------------------------------------
void writeJson(std::ostream &out);

} // namespace DeftLB

#endif
