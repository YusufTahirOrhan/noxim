/*
 * DEFT_LB: late-binding Vertical-Link routing, injection-time policies and
 * the DEFT_HEUR / DEFT_QL selection logic. See DeftLateBinding.h.
 */

#include "DeftLateBinding.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <limits>
#include <fstream>
#include <map>
#include <sstream>

#include "DeftTopology.h"
#include "DeftVerticalLinkLut.h"
#include "DeftVirtualNetwork.h"
#include "GlobalParams.h"
#include "ReservationTable.h"
#include "Router.h"

namespace DeftLB {

namespace {

const int DIR_NONE = 4;
// References: the instance size is set at run time (DeftTopology::configure).
const int &W = DeftTopology::FootprintWidth;
const int &H = DeftTopology::FootprintHeight;
const int &NVL = DeftTopology::VerticalLinkCount;
const int &NROUTERS = DeftTopology::TotalRouters;
const int &NCHIP_ROUTERS = DeftTopology::ChipletRouterCount;
const int QDIRS = DIRECTIONS + 2;   // N,E,S,W,LOCAL,HUB

const int DX[4] = {0, 1, 0, -1};
const int DY[4] = {-1, 0, 1, 0};

Config g_config;
std::vector<Router *> g_routers;     // sized to TotalRouters on first registration

// Learner with the lookahead heuristic's information (parameter ql_lookahead):
// 0: static estimate ql_hop_cost * hops_after(o); 1: 1 + best_continuation(o).
int g_ql_lookahead = 0;

// Optional statistics file (parameter stats_file); empty = off (default).
std::string g_stats_file;

// ---- statistics ----
unsigned long g_dead_end_events = 0;
std::vector<unsigned long> g_vl_down;   // sized to VerticalLinkCount on first use
std::vector<unsigned long> g_vl_up;
unsigned long g_adaptive_decisions = 0;
unsigned long g_selection_calls = 0;
unsigned long g_ql_updates = 0;
std::vector<double> g_delays_inter;
std::vector<double> g_delays_intra;

// ---- Q tables: [router][destination chiplet router][direction] ----
std::vector<float> g_q;
std::vector<unsigned char> g_q_init;

int opposite(int d)
{
    return (d + 2) % 4;
}

bool isInterposer(int id)
{
    return id >= NCHIP_ROUTERS;
}

VlMask bit(int vl)
{
    return (VlMask) 1 << vl;
}

void ensureVlCounters()
{
    if ((int) g_vl_down.size() != NVL) {
        g_vl_down.assign(NVL, 0);
        g_vl_up.assign(NVL, 0);
    }
}

int vlChipX(int vl)
{
    return footprintX(DeftTopology::chipletEndpointForVerticalLink(vl));
}

int vlChipY(int vl)
{
    return footprintY(DeftTopology::chipletEndpointForVerticalLink(vl));
}

int manhattanXY(int x0, int y0, int x1, int y1)
{
    return std::abs(x0 - x1) + std::abs(y0 - y1);
}

// ---- turn models (same definitions as the formal model) ----
bool legalTurn(int tm, int x, int last, int next)
{
    if (last == DIR_NONE)
        return true;
    if (next == opposite(last))
        return false;
    if (tm == TM_XY)
        return !((last == DIRECTION_NORTH || last == DIRECTION_SOUTH) &&
                 (next == DIRECTION_EAST || next == DIRECTION_WEST));
    // Chiu's odd-even turn model, column parity of the current node.
    const bool even = (x % 2) == 0;
    if (even && last == DIRECTION_EAST &&
        (next == DIRECTION_NORTH || next == DIRECTION_SOUTH))
        return false;
    if (!even && (last == DIRECTION_NORTH || last == DIRECTION_SOUTH) &&
        next == DIRECTION_WEST)
        return false;
    return true;
}

int productiveMask(int x, int y, int tx, int ty)
{
    int m = 0;
    if (tx > x) m |= 1 << DIRECTION_EAST;
    if (tx < x) m |= 1 << DIRECTION_WEST;
    if (ty > y) m |= 1 << DIRECTION_SOUTH;
    if (ty < y) m |= 1 << DIRECTION_NORTH;
    return m;
}

// reach cache: [tm][x][y][last][tx][ty] -> 0 unknown, 1 false, 2 true
// sized 2 x W x H x 5 x W x H on first use (W, H = footprint)
std::vector<unsigned char> g_reach;

bool reach(int tm, int x, int y, int last, int tx, int ty)
{
    if (x == tx && y == ty)
        return true;
    if (g_reach.empty())
        g_reach.assign((size_t) 2 * W * H * 5 * W * H, 0);
    unsigned char &c = g_reach[((((((size_t) tm * W + x) * H + y) * 5 + last) * W + tx) * H) + ty];
    if (c)
        return c == 2;
    bool ok = false;
    int prod = productiveMask(x, y, tx, ty);
    for (int d = 0; d < 4 && !ok; d++) {
        if (!(prod & (1 << d)))
            continue;
        if (!legalTurn(tm, x, last, d))
            continue;
        if (reach(tm, x + DX[d], y + DY[d], d, tx, ty))
            ok = true;
    }
    c = ok ? 2 : 1;
    return ok;
}

// ---- occupancy helpers ----
unsigned int bufferedFlits(int router_id)
{
    Router *r = routerById(router_id);
    return r ? r->getBufferedFlitCount() : 0;
}

unsigned int portFlits(int router_id, int port)
{
    Router *r = routerById(router_id);
    if (!r)
        return 0;
    unsigned int n = 0;
    for (int vc = 0; vc < GlobalParams::n_virtual_channels; vc++)
        n += r->buffer[port][vc].Size();
    return n;
}

double occExit(int vl)
{
    return bufferedFlits(DeftTopology::chipletEndpointForVerticalLink(vl)) +
           portFlits(DeftTopology::interposerEndpointForVerticalLink(vl), DIRECTION_HUB);
}

double occEntry(int vl)
{
    return bufferedFlits(DeftTopology::interposerEndpointForVerticalLink(vl)) +
           portFlits(DeftTopology::chipletEndpointForVerticalLink(vl), DIRECTION_HUB);
}

VlMask functionalMask(int chiplet_id)
{
    VlMask m = 0;
    std::vector<DeftTopology::VerticalLinkInfo> links =
        DeftTopology::functionalVerticalLinksForChiplet(chiplet_id);
    for (size_t i = 0; i < links.size(); i++)
        m |= bit(links[i].vl_id);
    return m;
}

int randomMember(VlMask mask)
{
    std::vector<int> members;
    for (int v = 0; v < NVL; v++)
        if (mask & bit(v))
            members.push_back(v);
    if (members.empty())
        return -1;
    return members[rand() % members.size()];
}

bool parsePolicy(const std::string &v, InjectionPolicy *p)
{
    if (v == "late") *p = POLICY_LATE;
    else if (v == "lut") *p = POLICY_LUT;
    else if (v == "random") *p = POLICY_RANDOM;
    else if (v == "mindist") *p = POLICY_MINDIST;
    else if (v == "oracle") *p = POLICY_ORACLE;
    else return false;
    return true;
}

bool isCostPolicy(InjectionPolicy p)
{
    return p == POLICY_MINDIST || p == POLICY_ORACLE;
}

// Injection-time choice of exit/entry masks for inter-chiplet packets.
void chooseMasks(int src, int dst, VlMask *exit_mask, VlMask *entry_mask)
{
    const Config &c = g_config;
    const VlMask fs = functionalMask(chipletOf(src));
    const VlMask fd = functionalMask(chipletOf(dst));

    VlMask es = fs, ed = fd;     // candidate sets after non-cost policies

    if (c.exit_policy == POLICY_LUT || c.entry_policy == POLICY_LUT) {
        DeftVerticalLinkLut::Entry entry;
        std::string err;
        if (!DeftVerticalLinkLut::lookup(chipletOf(src), src, chipletOf(dst), &entry, &err)) {
            std::cerr << "DEFT_LB: LUT lookup failed: " << err << std::endl;
            exit(1);
        }
        if (c.exit_policy == POLICY_LUT)
            es = bit(entry.source_exit.selected_vl_id);
        if (c.entry_policy == POLICY_LUT)
            ed = bit(entry.destination_entry.selected_vl_id);
    }
    if (c.exit_policy == POLICY_RANDOM)
        es = bit(randomMember(fs));
    if (c.entry_policy == POLICY_RANDOM)
        ed = bit(randomMember(fd));

    const bool exit_cost = isCostPolicy(c.exit_policy);
    const bool entry_cost = isCostPolicy(c.entry_policy);
    if (exit_cost || entry_cost) {
        const bool oracle = c.exit_policy == POLICY_ORACLE || c.entry_policy == POLICY_ORACLE;
        const int sx = footprintX(src), sy = footprintY(src);
        const int dx = footprintX(dst), dy = footprintY(dst);
        double best = std::numeric_limits<double>::max();
        std::vector<std::pair<int, int> > ties;
        for (int v = 0; v < NVL; v++) {
            if (!(es & bit(v)))
                continue;
            for (int e = 0; e < NVL; e++) {
                if (!(ed & bit(e)))
                    continue;
                double cost = manhattanXY(sx, sy, vlChipX(v), vlChipY(v)) +
                              manhattanXY(vlChipX(v), vlChipY(v), vlChipX(e), vlChipY(e)) +
                              manhattanXY(vlChipX(e), vlChipY(e), dx, dy);
                if (oracle) {
                    if (c.exit_policy == POLICY_ORACLE)
                        cost += c.oracle_beta * occExit(v);
                    if (c.entry_policy == POLICY_ORACLE)
                        cost += c.oracle_beta * occEntry(e);
                }
                if (cost < best - 1e-9) {
                    best = cost;
                    ties.clear();
                }
                if (cost < best + 1e-9)
                    ties.push_back(std::make_pair(v, e));
            }
        }
        std::pair<int, int> pick = ties[rand() % ties.size()];
        if (exit_cost)
            es = bit(pick.first);
        if (entry_cost)
            ed = bit(pick.second);
    }

    *exit_mask = es;
    *entry_mask = ed;
}

size_t qIndex(int router, int dst, int dir)
{
    return ((size_t) router * NCHIP_ROUTERS + dst) * QDIRS + dir;
}

void ensureQ()
{
    if (g_q.empty()) {
        g_q.assign((size_t) NROUTERS * NCHIP_ROUTERS * QDIRS, 0.0f);
        g_q_init.assign(g_q.size(), 0);
    }
}

double remoteEstimate(const RouteData &rd, int out_dir);   // defined with the selection logic
double remoteStatic(const RouteData &rd, int out_dir);

int pickMin(const std::vector<int> &dirs, const std::vector<double> &cost)
{
    double best = std::numeric_limits<double>::max();
    for (size_t k = 0; k < cost.size(); k++)
        best = std::min(best, cost[k]);
    std::vector<int> ties;
    for (size_t k = 0; k < cost.size(); k++)
        if (cost[k] < best + 1e-9)
            ties.push_back(dirs[k]);
    return ties[rand() % ties.size()];
}

double percentile(std::vector<double> v, double p)
{
    if (v.empty())
        return 0.0;
    std::sort(v.begin(), v.end());
    size_t k = (size_t) std::ceil(p * v.size());
    if (k == 0) k = 1;
    if (k > v.size()) k = v.size();
    return v[k - 1];
}

double mean(const std::vector<double> &v)
{
    if (v.empty())
        return 0.0;
    double s = 0;
    for (size_t i = 0; i < v.size(); i++)
        s += v[i];
    return s / v.size();
}

} // namespace

// ======================================================================

Config::Config()
    : exit_policy(POLICY_LUT), entry_policy(POLICY_LUT),
      chip_tm(TM_XY), ipos_tm(TM_XY),
      heur_w(1.0), heur_busy(4.0), heur_lookahead(0),
      ql_alpha(0.3), ql_eps(0.0), ql_hop_cost(1.0),
      ql_w(1.0), ql_busy(4.0), ql_key(0),
      oracle_beta(1.0)
{
}

Config &config()
{
    return g_config;
}

std::string policyName(InjectionPolicy p)
{
    switch (p) {
    case POLICY_LATE: return "late";
    case POLICY_LUT: return "lut";
    case POLICY_RANDOM: return "random";
    case POLICY_MINDIST: return "mindist";
    case POLICY_ORACLE: return "oracle";
    }
    return "?";
}

std::string turnModelName(int tm)
{
    return tm == TM_OE ? "OE" : "XY";
}

bool setParam(const std::string &key, const std::string &value,
              std::string *error_message)
{
    Config &c = g_config;
    if (key == "exit" || key == "entry") {
        InjectionPolicy p;
        if (!parsePolicy(value, &p)) {
            if (error_message) *error_message = "bad " + key + " policy " + value;
            return false;
        }
        (key == "exit" ? c.exit_policy : c.entry_policy) = p;
        return true;
    }
    if (key == "chip_tm" || key == "ipos_tm") {
        int tm;
        if (value == "XY") tm = TM_XY;
        else if (value == "OE") tm = TM_OE;
        else {
            if (error_message) *error_message = "bad turn model " + value;
            return false;
        }
        (key == "chip_tm" ? c.chip_tm : c.ipos_tm) = tm;
        return true;
    }
    if (key == "stats_file") {         // statistics only (bottleneck diagnosis); off by default
        g_stats_file = value;
        return true;
    }
    char *end = 0;
    double d = strtod(value.c_str(), &end);
    if (end == value.c_str()) {
        if (error_message) *error_message = "bad numeric value for " + key;
        return false;
    }
    if (key == "heur_w") c.heur_w = d;
    else if (key == "heur_busy") c.heur_busy = d;
    else if (key == "heur_lookahead") c.heur_lookahead = (int) d;
    else if (key == "ql_alpha") c.ql_alpha = d;
    else if (key == "ql_eps") c.ql_eps = d;
    else if (key == "ql_hop_cost") c.ql_hop_cost = d;
    else if (key == "ql_w") c.ql_w = d;
    else if (key == "ql_busy") c.ql_busy = d;
    else if (key == "ql_key") c.ql_key = (int) d;
    else if (key == "ql_lookahead") {
        if (d != 0.0 && d != 1.0) {
            if (error_message) *error_message = "ql_lookahead must be 0 or 1";
            return false;
        }
        g_ql_lookahead = (int) d;
    }
    else if (key == "oracle_beta") c.oracle_beta = d;
    else {
        if (error_message) *error_message = "unknown DEFT_LB parameter " + key;
        return false;
    }
    return true;
}

bool isActive()
{
    return GlobalParams::topology == TOPOLOGY_DEFT_2_5D &&
           GlobalParams::routing_algorithm == "DEFT_LB";
}

bool qLearningEnabled()
{
    return isActive() && GlobalParams::selection_strategy == "DEFT_QL";
}

bool validateConfiguration(std::string *error_message)
{
    const Config &c = g_config;
    if (c.exit_policy == POLICY_LATE && c.entry_policy != POLICY_LATE) {
        if (error_message)
            *error_message = "late exit requires late entry (exit late / entry fixed is not a checked relation)";
        return false;
    }
    if ((c.exit_policy == POLICY_LUT || c.entry_policy == POLICY_LUT) &&
        !DeftVerticalLinkLut::isLoaded()) {
        if (error_message)
            *error_message = "policy lut requires -deft_vl_lut";
        return false;
    }
    if (c.exit_policy == POLICY_LATE && c.chip_tm != TM_OE && c.chip_tm != TM_XY) {
        if (error_message) *error_message = "bad chiplet turn model";
        return false;
    }
    return true;
}

// ---- registry ----
void registerRouter(int id, Router *router)
{
    if ((int) g_routers.size() != NROUTERS)
        g_routers.assign(NROUTERS, (Router *) 0);
    if (id >= 0 && id < NROUTERS)
        g_routers[id] = router;
}

Router *routerById(int id)
{
    if (id < 0 || id >= (int) g_routers.size())
        return 0;
    return g_routers[id];
}

// ---- geometry ----
int footprintX(int id)
{
    return (isInterposer(id) ? id - NCHIP_ROUTERS : id) % W;
}

int footprintY(int id)
{
    return (isInterposer(id) ? id - NCHIP_ROUTERS : id) / W;
}

int chipletOf(int id)
{
    if (isInterposer(id))
        return -1;
    return (footprintY(id) / DeftTopology::ChipletLocalHeight) * DeftTopology::ChipletGridWidth +
           footprintX(id) / DeftTopology::ChipletLocalWidth;
}

int vlAtRouter(int id)
{
    const DeftTopology::VerticalLinkInfo *l = isInterposer(id) ?
        DeftTopology::verticalLinkForInterposerRouter(id) :
        DeftTopology::verticalLinkForBoundaryRouter(id);
    return l ? l->vl_id : -1;
}

int neighborId(int id, int out_dir)
{
    if (out_dir == DIRECTION_HUB)
        return isInterposer(id) ? id - NCHIP_ROUTERS : id + NCHIP_ROUTERS;
    if (out_dir < 0 || out_dir > 3)
        return -1;
    int x = footprintX(id) + DX[out_dir];
    int y = footprintY(id) + DY[out_dir];
    if (x < 0 || x >= W || y < 0 || y >= H)
        return -1;
    return (isInterposer(id) ? NCHIP_ROUTERS : 0) + y * W + x;
}

int arrivalPort(int out_dir)
{
    if (out_dir == DIRECTION_HUB)
        return DIRECTION_HUB;
    return opposite(out_dir);
}

int lastMoveFromDirIn(int dir_in)
{
    if (dir_in >= 0 && dir_in <= 3)
        return opposite(dir_in);
    return DIR_NONE;
}

int manhattan(int a, int b)
{
    return manhattanXY(footprintX(a), footprintY(a), footprintX(b), footprintY(b));
}

int movesMask(int tm, int x, int y, int last, int tx, int ty)
{
    int prod = productiveMask(x, y, tx, ty);
    if (tm == TM_XY) {
        int xm = prod & ((1 << DIRECTION_EAST) | (1 << DIRECTION_WEST));
        if (xm)
            prod = xm;
    }
    int out = 0;
    for (int d = 0; d < 4; d++) {
        if (!(prod & (1 << d)))
            continue;
        if (!legalTurn(tm, x, last, d))
            continue;
        if (!reach(tm, x + DX[d], y + DY[d], d, tx, ty))
            continue;
        out |= 1 << d;
    }
    return out;
}

// ---- routing relation ----
namespace {

enum Phase { PH_INTRA, PH_SOURCE, PH_IPOS, PH_DEST, PH_INVALID };

Phase phaseOf(int cur, int src, int dst)
{
    const int cs = chipletOf(src), cd = chipletOf(dst);
    if (cs < 0 || cd < 0)
        return PH_INVALID;
    if (isInterposer(cur))
        return cs == cd ? PH_INVALID : PH_IPOS;
    const int cc = chipletOf(cur);
    if (cs == cd)
        return cc == cs ? PH_INTRA : PH_INVALID;
    if (cc == cs) return PH_SOURCE;
    if (cc == cd) return PH_DEST;
    return PH_INVALID;
}

int movesTowardsMask(int tm, int cur, int last, VlMask cand_mask, int skip_vl)
{
    int out = 0;
    const int x = footprintX(cur), y = footprintY(cur);
    for (int v = 0; v < NVL; v++) {
        if (!(cand_mask & bit(v)) || v == skip_vl)
            continue;
        out |= movesMask(tm, x, y, last, vlChipX(v), vlChipY(v));
    }
    return out;
}

} // namespace

void legalMoves(const RouteData &rd, std::vector<int> *dirs)
{
    dirs->clear();
    const int cur = rd.current_id;
    const int last = lastMoveFromDirIn(rd.dir_in);
    int m = 0;
    switch (phaseOf(cur, rd.src_id, rd.dst_id)) {
    case PH_INTRA:
    case PH_DEST:
        m = movesMask(g_config.chip_tm, footprintX(cur), footprintY(cur), last,
                      footprintX(rd.dst_id), footprintY(rd.dst_id));
        break;
    case PH_SOURCE: {
        const VlMask cand = rd.deft_exit_mask;
        const int here = vlAtRouter(cur);
        if (here >= 0 && (cand & bit(here))) {
            dirs->push_back(DIRECTION_HUB);
            if (cand == bit(here))
                return;   // committed to this VL
        }
        m = movesTowardsMask(g_config.chip_tm, cur, last, cand, here);
        break;
    }
    case PH_IPOS: {
        const VlMask cand = rd.deft_entry_mask;
        const int here = vlAtRouter(cur);
        if (here >= 0 && (cand & bit(here))) {
            dirs->push_back(DIRECTION_HUB);
            if (cand == bit(here))
                return;
        }
        m = movesTowardsMask(g_config.ipos_tm, cur, last, cand, here);
        break;
    }
    default:
        return;
    }
    for (int d = 0; d < 4; d++)
        if (m & (1 << d))
            dirs->push_back(d);
}

void nextMasks(int cur, int dir_in, int out_dir, int src, int dst,
               VlMask exit_mask, VlMask entry_mask,
               VlMask *next_exit, VlMask *next_entry)
{
    *next_exit = exit_mask;
    *next_entry = entry_mask;
    const Phase ph = phaseOf(cur, src, dst);
    if (ph != PH_SOURCE && ph != PH_IPOS)
        return;
    const int here = vlAtRouter(cur);
    const VlMask cand = ph == PH_SOURCE ? exit_mask : entry_mask;
    VlMask pruned;
    if (out_dir == DIRECTION_HUB) {
        pruned = bit(here);
    } else {
        const int tm = ph == PH_SOURCE ? g_config.chip_tm : g_config.ipos_tm;
        const int last = lastMoveFromDirIn(dir_in);
        const int x = footprintX(cur), y = footprintY(cur);
        pruned = 0;
        for (int v = 0; v < NVL; v++) {
            if (!(cand & bit(v)) || v == here)
                continue;
            if (movesMask(tm, x, y, last, vlChipX(v), vlChipY(v)) & (1 << out_dir))
                pruned |= bit(v);
        }
    }
    if (ph == PH_SOURCE)
        *next_exit = pruned;
    else
        *next_entry = pruned;
}

int remainingHops(int cur, int src, int dst, VlMask exit_mask, VlMask entry_mask)
{
    switch (phaseOf(cur, src, dst)) {
    case PH_INTRA:
    case PH_DEST:
        return manhattan(cur, dst);
    case PH_IPOS: {
        int best = 1 << 20;
        for (int e = 0; e < NVL; e++)
            if (entry_mask & bit(e))
                best = std::min(best, manhattanXY(footprintX(cur), footprintY(cur), vlChipX(e), vlChipY(e)) + 1 +
                                          manhattanXY(vlChipX(e), vlChipY(e), footprintX(dst), footprintY(dst)));
        return best;
    }
    case PH_SOURCE: {
        int best = 1 << 20;
        for (int v = 0; v < NVL; v++) {
            if (!(exit_mask & bit(v)))
                continue;
            for (int e = 0; e < NVL; e++) {
                if (!(entry_mask & bit(e)))
                    continue;
                int h = manhattanXY(footprintX(cur), footprintY(cur), vlChipX(v), vlChipY(v)) + 1 +
                        manhattanXY(vlChipX(v), vlChipY(v), vlChipX(e), vlChipY(e)) + 1 +
                        manhattanXY(vlChipX(e), vlChipY(e), footprintX(dst), footprintY(dst));
                best = std::min(best, h);
            }
        }
        return best;
    }
    default:
        return 1 << 20;
    }
}

int hopsAfterMove(const RouteData &rd, int out_dir)
{
    const int n = neighborId(rd.current_id, out_dir);
    if (n < 0)
        return 1 << 20;
    VlMask ne, nn;
    nextMasks(rd.current_id, rd.dir_in, out_dir, rd.src_id, rd.dst_id,
              rd.deft_exit_mask, rd.deft_entry_mask, &ne, &nn);
    return 1 + remainingHops(n, rd.src_id, rd.dst_id, ne, nn);
}

RouteData nextRouteData(const RouteData &rd, int out_dir, int out_vc)
{
    RouteData n = rd;
    n.current_id = neighborId(rd.current_id, out_dir);
    n.dir_in = arrivalPort(out_dir);
    n.vc_id = out_vc;
    nextMasks(rd.current_id, rd.dir_in, out_dir, rd.src_id, rd.dst_id,
              rd.deft_exit_mask, rd.deft_entry_mask,
              &n.deft_exit_mask, &n.deft_entry_mask);
    return n;
}

void legalOutputsWithVn(const RouteData &rd, std::vector<int> *dirs)
{
    std::vector<int> all;
    legalMoves(rd, &all);
    dirs->clear();
    for (size_t i = 0; i < all.size(); i++)
        if (DeftVirtualNetwork::isOutputDirectionAllowed(rd, all[i]))
            dirs->push_back(all[i]);
}

// ---- injection ----
void prepareHeadPacket(Packet &p)
{
    if (!DeftVirtualNetwork::isEnabled())
        return;
    VlMask exit_mask = 0, entry_mask = 0;
    if (isActive() && chipletOf(p.src_id) >= 0 && chipletOf(p.dst_id) >= 0 &&
        chipletOf(p.src_id) != chipletOf(p.dst_id)) {
        chooseMasks(p.src_id, p.dst_id, &exit_mask, &entry_mask);
    }
    p.deft_exit_mask = exit_mask;
    p.deft_entry_mask = entry_mask;
    p.vc_id = DeftVirtualNetwork::assignSourceVirtualNetwork(p.src_id, p.dst_id, exit_mask);
}

// ---- optional statistics (parameter stats_file; off by default) ----
// Observation only: nothing here feeds back into routing, selection or flow control.
namespace {

struct RouterStat {
    unsigned long heads;            // head flits forwarded (all outputs)
    double resid_sum;               // sum of (forward cycle - arrival in the input buffer)
    double front_sum;               // sum of (forward cycle - arrival at the buffer front)
    unsigned long fwd[DIRECTIONS + 2];   // heads forwarded per output: N, E, S, W, LOCAL, HUB
};

struct PacketTrack {
    int hops, exit_used, entry_used, lut_exit, lut_entry, exit_fix_rem, entry_fix_rem, ipos_hops, ipos_hops_at_fix;
    PacketTrack() : hops(0), exit_used(-1), entry_used(-1), lut_exit(-1), lut_entry(-1),
                    exit_fix_rem(-1), entry_fix_rem(-1), ipos_hops(0), ipos_hops_at_fix(-1) {}
};

std::vector<RouterStat> g_rstat;
std::map<std::pair<int, double>, PacketTrack> g_ptrack;
std::map<int, unsigned long> g_extra_hops_hist, g_entry_fix_hist, g_exit_fix_hist, g_entry_fix_ipos_hops_hist;
unsigned long g_st_inter = 0, g_st_entry_diff = 0, g_st_exit_diff = 0, g_st_lut_known = 0;

bool statsOn()
{
    return !g_stats_file.empty();
}

bool measuring(double now)
{
    return now - GlobalParams::reset_time >= GlobalParams::stats_warm_up_time;
}

int popcount(VlMask m)
{
    return __builtin_popcountll(m);
}

void statsForward(Router *router, int dir_in, int out_dir, const Flit &flit, double now, double front_cycle,
                  VlMask exit_before, VlMask entry_before, VlMask exit_after, VlMask entry_after)
{
    (void) dir_in;
    const int cur = router->local_id;
    if ((int) g_rstat.size() != NROUTERS)
        g_rstat.assign(NROUTERS, RouterStat());
    if (measuring(now)) {
        RouterStat &rs = g_rstat[cur];
        rs.heads++;
        rs.resid_sum += now - flit.arrival_cycle;
        rs.front_sum += now - front_cycle;
        if (out_dir >= 0 && out_dir < DIRECTIONS + 2)
            rs.fwd[out_dir]++;
    }
    if (out_dir == DIRECTION_LOCAL)
        return;
    const int src = flit.src_id, dst = flit.dst_id;
    if (chipletOf(src) < 0 || chipletOf(dst) < 0 || chipletOf(src) == chipletOf(dst))
        return;
    std::pair<int, double> k(src, flit.timestamp);
    std::map<std::pair<int, double>, PacketTrack>::iterator it = g_ptrack.find(k);
    if (it == g_ptrack.end()) {
        it = g_ptrack.insert(std::make_pair(k, PacketTrack())).first;
        if (DeftVerticalLinkLut::isLoaded()) {
            DeftVerticalLinkLut::Entry e;
            if (DeftVerticalLinkLut::lookup(chipletOf(src), src, chipletOf(dst), &e, 0)) {
                it->second.lut_exit = e.source_exit.selected_vl_id;
                it->second.lut_entry = e.destination_entry.selected_vl_id;
            }
        }
    }
    PacketTrack &t = it->second;
    t.hops++;
    const int next = neighborId(cur, out_dir);
    if (isInterposer(cur)) {
        if (out_dir == DIRECTION_HUB) {
            t.entry_used = vlAtRouter(cur);
            if (popcount(entry_before) > 1 && t.entry_fix_rem < 0) {
                t.entry_fix_rem = 0;            // fixed by taking this VL while others were open
                t.ipos_hops_at_fix = t.ipos_hops;
            }
        } else {
            if (popcount(entry_before) > 1 && popcount(entry_after) == 1 && t.entry_fix_rem < 0) {
                int e = 0;
                while (!(entry_after >> e & 1)) e++;
                t.entry_fix_rem = manhattan(next, DeftTopology::interposerEndpointForVerticalLink(e));
                t.ipos_hops_at_fix = t.ipos_hops + 1;
            }
            t.ipos_hops++;
        }
    } else if (chipletOf(cur) == chipletOf(src)) {
        if (out_dir == DIRECTION_HUB) {
            t.exit_used = vlAtRouter(cur);
            if (popcount(exit_before) > 1 && t.exit_fix_rem < 0)
                t.exit_fix_rem = 0;
        } else if (popcount(exit_before) > 1 && popcount(exit_after) == 1 && t.exit_fix_rem < 0) {
            int v = 0;
            while (!(exit_after >> v & 1)) v++;
            t.exit_fix_rem = manhattan(next, DeftTopology::chipletEndpointForVerticalLink(v));
        }
    }
}

void statsConsumed(const Flit &flit, double now)
{
    std::map<std::pair<int, double>, PacketTrack>::iterator it =
        g_ptrack.find(std::make_pair(flit.src_id, flit.timestamp));
    if (it == g_ptrack.end())
        return;
    const PacketTrack &t = it->second;
    if (measuring(now)) {
        g_st_inter++;
        if (t.lut_exit >= 0 && t.lut_entry >= 0) {
            g_st_lut_known++;
            g_st_exit_diff += t.exit_used != t.lut_exit;
            g_st_entry_diff += t.entry_used != t.lut_entry;
            const int lut_hops =
                manhattan(flit.src_id, DeftTopology::chipletEndpointForVerticalLink(t.lut_exit)) + 1 +
                manhattan(DeftTopology::chipletEndpointForVerticalLink(t.lut_exit),
                          DeftTopology::chipletEndpointForVerticalLink(t.lut_entry)) + 1 +
                manhattan(DeftTopology::chipletEndpointForVerticalLink(t.lut_entry), flit.dst_id);
            g_extra_hops_hist[t.hops - lut_hops]++;
        }
        g_entry_fix_hist[t.entry_fix_rem]++;           // -1: fixed before the interposer
        g_exit_fix_hist[t.exit_fix_rem]++;             // -1: fixed at injection
        g_entry_fix_ipos_hops_hist[t.ipos_hops_at_fix]++;
    }
    g_ptrack.erase(it);
}

void writeHist(std::ostream &o, const char *name, const std::map<int, unsigned long> &h, bool last)
{
    o << "  \"" << name << "\": {";
    bool first = true;
    for (std::map<int, unsigned long>::const_iterator it = h.begin(); it != h.end(); ++it) {
        o << (first ? "" : ", ") << "\"" << it->first << "\": " << it->second;
        first = false;
    }
    o << "}" << (last ? "" : ",") << std::endl;
}

void writeStatsFile()
{
    std::ofstream o(g_stats_file.c_str());
    if (!o)
        return;
    o << "{" << std::endl;
    o << "  \"measured_cycles\": " << GlobalParams::simulation_time - GlobalParams::stats_warm_up_time << "," << std::endl;
    o << "  \"packet_size_flits\": " << GlobalParams::min_packet_size << "," << std::endl;
    o << "  \"inter_packets\": " << g_st_inter << ", \"lut_known\": " << g_st_lut_known
      << ", \"exit_differs_from_lut\": " << g_st_exit_diff << ", \"entry_differs_from_lut\": " << g_st_entry_diff
      << "," << std::endl;
    writeHist(o, "extra_hops_vs_lut_path", g_extra_hops_hist, false);
    writeHist(o, "entry_fixed_remaining_hops", g_entry_fix_hist, false);
    writeHist(o, "entry_fixed_after_interposer_hops", g_entry_fix_ipos_hops_hist, false);
    writeHist(o, "exit_fixed_remaining_hops", g_exit_fix_hist, false);
    o << "  \"routers\": [" << std::endl;
    for (int id = 0; id < (int) g_rstat.size(); id++) {
        const RouterStat &r = g_rstat[id];
        const char *cls = isInterposer(id) ? (vlAtRouter(id) >= 0 ? "ipos_vl" : "ipos_interior")
                                           : (vlAtRouter(id) >= 0 ? "chip_vl" : "chip_interior");
        o << "    {\"id\": " << id << ", \"class\": \"" << cls << "\", \"x\": " << footprintX(id)
          << ", \"y\": " << footprintY(id) << ", \"heads\": " << r.heads << ", \"resid_sum\": " << r.resid_sum
          << ", \"front_sum\": " << r.front_sum << ", \"fwd\": [";
        for (int d = 0; d < DIRECTIONS + 2; d++)
            o << (d ? ", " : "") << r.fwd[d];
        o << "]}" << (id + 1 < (int) g_rstat.size() ? "," : "") << std::endl;
    }
    o << "  ]" << std::endl << "}" << std::endl;
}

} // namespace

// ---- router hooks ----
void onHeadForward(Router *router, int dir_in, int out_dir, int out_vc,
                   Flit *flit, double now, double front_cycle)
{
    if (statsOn() && isActive() && out_dir == DIRECTION_LOCAL)
        statsForward(router, dir_in, out_dir, *flit, now, front_cycle, 0, 0, 0, 0);
    if (!isActive() || out_dir == DIRECTION_LOCAL)
        return;
    const int cur = router->local_id;

    if (out_dir == DIRECTION_HUB) {
        const int v = vlAtRouter(cur);
        if (v >= 0) {
            ensureVlCounters();
            if (isInterposer(cur)) g_vl_up[v]++;
            else g_vl_down[v]++;
        }
    }

    RouteData rd;
    rd.current_id = cur;
    rd.src_id = flit->src_id;
    rd.dst_id = flit->dst_id;
    rd.dir_in = dir_in;
    rd.vc_id = flit->vc_id;
    rd.deft_exit_mask = flit->deft_exit_mask;
    rd.deft_entry_mask = flit->deft_entry_mask;

    if (qLearningEnabled() && rd.dst_id < NCHIP_ROUTERS) {
        remoteEstimate(rd, out_dir);   // make sure the entry exists (lazy initialisation)
        flit->ql_prev_router = cur;
        flit->ql_prev_dir = out_dir;
        flit->ql_prev_static = remoteStatic(rd, out_dir);
    }

    RouteData nrd = nextRouteData(rd, out_dir, out_vc);
    if (statsOn())
        statsForward(router, dir_in, out_dir, *flit, now, front_cycle, rd.deft_exit_mask, rd.deft_entry_mask,
                     nrd.deft_exit_mask, nrd.deft_entry_mask);
    flit->deft_exit_mask = nrd.deft_exit_mask;
    flit->deft_entry_mask = nrd.deft_entry_mask;
}

void onRouteFailure(int router_id, const Flit &flit)
{
    (void) router_id;
    (void) flit;
    g_dead_end_events++;
}

void onHeadConsumed(const Flit &flit, double now)
{
    if (statsOn())
        statsConsumed(flit, now);
    if (now - GlobalParams::reset_time < GlobalParams::stats_warm_up_time)
        return;
    const double d = now - flit.timestamp;
    if (chipletOf(flit.src_id) >= 0 && chipletOf(flit.src_id) == chipletOf(flit.dst_id))
        g_delays_intra.push_back(d);
    else
        g_delays_inter.push_back(d);
}

// ---- selection ----
namespace {

double downstreamOccupancy(Router *router, int out_dir, int out_vc)
{
    const int n = neighborId(router->local_id, out_dir);
    Router *r = routerById(n);
    if (!r)
        return 0.0;
    return r->buffer[arrivalPort(out_dir)][out_vc].Size();
}

bool outputVcBusy(Router *router, const RouteData &rd, int out_dir, int out_vc)
{
    TReservation r;
    r.input = rd.dir_in;
    r.vc = rd.vc_id;
    r.output_vc = out_vc;
    return router->reservation_table.checkReservation(r, out_dir) == RT_OUTVC_BUSY;
}

int outputVc(const RouteData &rd, int out_dir)
{
    return DeftVirtualNetwork::selectOutputVirtualNetwork(rd, out_dir, 0);
}

// Local observation shared by the heuristic and the learner: flits waiting in
// the downstream input buffer (what a credit counter reports) and whether the
// output VC is currently held by another packet.
double localCost(Router *router, const RouteData &rd, int out_dir, double w, double busy)
{
    const int ovc = outputVc(rd, out_dir);
    double c = w * downstreamOccupancy(router, out_dir, ovc);
    if (outputVcBusy(router, rd, out_dir, ovc))
        c += busy;
    return c;
}

// One-hop lookahead term of DEFT_HEUR with heur_lookahead 1: the cheapest
// continuation at the neighbour reached through o, using the neighbour's
// downstream occupancy weighted by w.
double bestContinuation(const RouteData &rd, int o, double w)
{
    const int ovc = outputVc(rd, o);
    RouteData nrd = nextRouteData(rd, o, ovc);
    Router *nr = routerById(nrd.current_id);
    double best;
    if (nrd.current_id == rd.dst_id || !nr) {
        best = 0.0;
    } else {
        std::vector<int> nd;
        legalOutputsWithVn(nrd, &nd);
        best = std::numeric_limits<double>::max();
        for (size_t j = 0; j < nd.size(); j++) {
            const int z = nd[j];
            double cz = hopsAfterMove(nrd, z) +
                        w * downstreamOccupancy(nr, z, outputVc(nrd, z));
            best = std::min(best, cz);
        }
        if (nd.empty())
            best = remainingHops(nrd.current_id, nrd.src_id, nrd.dst_id,
                                 nrd.deft_exit_mask, nrd.deft_entry_mask);
    }
    return best;
}

// Static part of the learner's remote estimate; the learned residual is
// kept over it (and stored in ql_prev_static when the head is forwarded).
double remoteStatic(const RouteData &rd, int out_dir)
{
    if (g_ql_lookahead)
        return 1.0 + bestContinuation(rd, out_dir, g_config.ql_w);
    return g_config.ql_hop_cost * hopsAfterMove(rd, out_dir);
}

// Learned estimate of the time from leaving through out_dir to delivery,
// excluding the local wait (which is observed directly).
double remoteEstimate(const RouteData &rd, int out_dir)
{
    ensureQ();
    const double stat = remoteStatic(rd, out_dir);
    const int key = g_config.ql_key ? chipletOf(rd.dst_id) : rd.dst_id;
    const size_t i = qIndex(rd.current_id, key, out_dir);
    // The table holds the learned residual over the static hop estimate,
    // so with alpha = 0 the learner reduces exactly to the heuristic.
    return stat + g_q[i];
}

double learnerCost(Router *router, const RouteData &rd, int out_dir)
{
    return localCost(router, rd, out_dir, g_config.ql_w, g_config.ql_busy) +
           remoteEstimate(rd, out_dir);
}

} // namespace

void onHeadAtFront(Router *router, int dir_in, const Flit &flit, double now)
{
    if (!qLearningEnabled() || flit.ql_prev_router < 0 || flit.dst_id >= NCHIP_ROUTERS)
        return;
    const int cur = router->local_id;
    double v_here = 0.0;
    if (cur != flit.dst_id) {
        RouteData rd;
        rd.current_id = cur;
        rd.src_id = flit.src_id;
        rd.dst_id = flit.dst_id;
        rd.dir_in = dir_in;
        rd.vc_id = flit.vc_id;
        rd.deft_exit_mask = flit.deft_exit_mask;
        rd.deft_entry_mask = flit.deft_entry_mask;
        std::vector<int> nd;
        legalOutputsWithVn(rd, &nd);
        if (nd.empty()) {
            v_here = g_config.ql_hop_cost *
                     remainingHops(cur, rd.src_id, rd.dst_id, rd.deft_exit_mask, rd.deft_entry_mask);
        } else {
            v_here = std::numeric_limits<double>::max();
            for (size_t k = 0; k < nd.size(); k++)
                v_here = std::min(v_here, learnerCost(router, rd, nd[k]));
        }
    }
    (void) now;
    // Remote part of the previous router's choice: the link plus this
    // router's own cost-to-go estimate (its observed local cost plus its
    // learned remote estimate). The time spent behind other flits here is
    // not added: the previous router already observed it as downstream
    // occupancy in its local term.
    const double target = 1.0 + v_here;
    ensureQ();
    const int key = g_config.ql_key ? chipletOf(flit.dst_id) : flit.dst_id;
    const size_t i = qIndex(flit.ql_prev_router, key, flit.ql_prev_dir);
    const double goal = target - flit.ql_prev_static;
    g_q[i] = (float) (g_q[i] + g_config.ql_alpha * (goal - g_q[i]));
    g_ql_updates++;
}

int selectHeuristic(Router *router, const std::vector<int> &dirs,
                    const RouteData &rd)
{
    g_selection_calls++;
    if (dirs.size() > 1)
        g_adaptive_decisions++;
    std::vector<double> cost(dirs.size(), 0.0);
    for (size_t k = 0; k < dirs.size(); k++) {
        const int o = dirs[k];
        double c = localCost(router, rd, o, g_config.heur_w, g_config.heur_busy);
        if (!g_config.heur_lookahead) {
            c += hopsAfterMove(rd, o);
        } else {
            // One-hop lookahead: cheapest continuation at the neighbour,
            // using the neighbour's downstream occupancy (one more hop of information).
            c += 1.0 + bestContinuation(rd, o, g_config.heur_w);
        }
        cost[k] = c;
    }
    return pickMin(dirs, cost);
}

int selectQLearning(Router *router, const std::vector<int> &dirs,
                    const RouteData &rd)
{
    g_selection_calls++;
    if (dirs.size() > 1)
        g_adaptive_decisions++;
    if (g_config.ql_eps > 0 && ((double) rand() / RAND_MAX) < g_config.ql_eps)
        return dirs[rand() % dirs.size()];
    std::vector<double> cost(dirs.size(), 0.0);
    for (size_t k = 0; k < dirs.size(); k++)
        cost[k] = learnerCost(router, rd, dirs[k]);
    return pickMin(dirs, cost);
}

// ---- statistics ----
void writeJson(std::ostream &out)
{
    const Config &c = g_config;
    out << "  \"deft_lb\": {" << std::endl;
    out << "    \"active\": " << (isActive() ? "true" : "false") << "," << std::endl;
    out << "    \"selection_strategy\": \"" << GlobalParams::selection_strategy << "\"," << std::endl;
    out << "    \"exit_policy\": \"" << policyName(c.exit_policy) << "\"," << std::endl;
    out << "    \"entry_policy\": \"" << policyName(c.entry_policy) << "\"," << std::endl;
    out << "    \"chip_tm\": \"" << turnModelName(c.chip_tm) << "\"," << std::endl;
    out << "    \"ipos_tm\": \"" << turnModelName(c.ipos_tm) << "\"," << std::endl;
    out << "    \"heur_w\": " << c.heur_w << ", \"heur_busy\": " << c.heur_busy
        << ", \"heur_lookahead\": " << c.heur_lookahead << "," << std::endl;
    out << "    \"ql_alpha\": " << c.ql_alpha << ", \"ql_eps\": " << c.ql_eps
        << ", \"ql_hop_cost\": " << c.ql_hop_cost << ", \"ql_w\": " << c.ql_w << ", \"ql_busy\": " << c.ql_busy
        << ", \"ql_key\": " << c.ql_key << ", \"ql_lookahead\": " << g_ql_lookahead
        << ", \"oracle_beta\": " << c.oracle_beta << "," << std::endl;
    out << "    \"dead_end_events\": " << g_dead_end_events << "," << std::endl;
    out << "    \"selection_calls\": " << g_selection_calls << "," << std::endl;
    out << "    \"adaptive_decisions\": " << g_adaptive_decisions << "," << std::endl;
    out << "    \"ql_updates\": " << g_ql_updates << "," << std::endl;
    ensureVlCounters();
    out << "    \"vl_down_packets\": [";
    for (int v = 0; v < NVL; v++) out << (v ? ", " : "") << g_vl_down[v];
    out << "]," << std::endl;
    out << "    \"vl_up_packets\": [";
    for (int v = 0; v < NVL; v++) out << (v ? ", " : "") << g_vl_up[v];
    out << "]," << std::endl;
    std::vector<double> all = g_delays_inter;
    all.insert(all.end(), g_delays_intra.begin(), g_delays_intra.end());
    out << "    \"packets_measured\": " << all.size() << "," << std::endl;
    out << "    \"delay_mean\": " << mean(all) << "," << std::endl;
    out << "    \"delay_p50\": " << percentile(all, 0.50) << "," << std::endl;
    out << "    \"delay_p95\": " << percentile(all, 0.95) << "," << std::endl;
    out << "    \"delay_p99\": " << percentile(all, 0.99) << "," << std::endl;
    out << "    \"delay_inter_mean\": " << mean(g_delays_inter) << "," << std::endl;
    out << "    \"delay_inter_p99\": " << percentile(g_delays_inter, 0.99) << "," << std::endl;
    out << "    \"delay_intra_mean\": " << mean(g_delays_intra) << "," << std::endl;
    out << "    \"packets_inter\": " << g_delays_inter.size() << "," << std::endl;
    out << "    \"packets_intra\": " << g_delays_intra.size() << std::endl;
    out << "  }" << std::endl;
    if (statsOn())
        writeStatsFile();
}

} // namespace DeftLB
