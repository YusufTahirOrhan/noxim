/*
 * DEFT_LB: late-binding Vertical-Link routing, injection-time policies and
 * the DEFT_HEUR / DEFT_QL selection logic. See DeftLateBinding.h.
 */

#include "DeftLateBinding.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <limits>
#include <deque>
#include <fstream>
#include <map>
#include <random>
#include <sstream>

#include <yaml-cpp/yaml.h>

#include "DeftTopology.h"
#include "DeftVerticalLinkLut.h"
#include "DeftVirtualNetwork.h"
#include "NetraceDriver.h"
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

// Weight of a horizontal interposer hop in the selection's static remaining-path length
// (parameter hop_weight_ipos, default 1.0 = plain hop count).
double g_hop_weight_ipos = 1.0;

// ---- v10 baselines (all off by default) ----
// MTR tables (parameter mtr_table): chiplet-local router index -> VL slot (0..3).
std::vector<int> g_mtr_out, g_mtr_in;
std::string g_mtr_file;
// Separate RNG for the 'ran' policy, so that rand() (traffic generation) is not perturbed.
std::mt19937 g_ran_rng;
bool g_ran_seeded = false;
// RC: outbound injection permission and RC buffer (parameters rc, rc_slots).
bool g_rc = false;
int g_rc_slots = 4;
struct RcState {
    int used;
    std::deque<int> queue;     // waiting source PEs, FIFO
    RcState() : used(0) {}
};
std::vector<RcState> g_rc_state;          // per chiplet router id (boundary routers used)
std::vector<double> g_rc_ready;           // per PE: cycle from which the granted packet may leave (-1 = none)
std::vector<double> g_rc_first_request;   // per PE: cycle of the pending request (-1 = none)
unsigned long g_rc_grants = 0;
double g_rc_wait_sum = 0.0;
// Plain DEFT VL counter (parameter count_vl).
bool g_count_vl = false;

// Optional statistics file (parameter stats_file); empty = off (default).
std::string g_stats_file;
// v23: lookahead routing (parameter lookahead_route) and the herding guard (parameter hysteresis); both off by default.
int g_lookahead_route = 0;
double g_hysteresis = 0.0;
unsigned long g_la_stored = 0, g_la_used = 0, g_la_mismatch = 0;
// v24 (all off by default): the penalty on outputs that drop DeFT-P's VL (parameter lut_bias), the lookahead fallback
// (parameter lookahead_fallback) and the busy term read from the reservation entries (parameter busy_state).
double g_lut_bias = 0.0;
int g_lookahead_fallback = 0;
int g_busy_state = 0;
bool g_asking_absent = false;        // the selection is being evaluated for a head that is not in the router yet (lookahead routing)
unsigned long g_la_multi = 0;        // stored decisions used at a hop that offers more than one output
unsigned long g_fb_checks = 0, g_fb_blocked = 0, g_fb_requests = 0, g_fb_taken = 0;
std::vector<int> g_default_exit;     // [source router * chiplets + destination chiplet] -> DeFT-P's exit VL (-2 = not looked up)
std::vector<int> g_default_entry;    // [destination router] -> DeFT-P's entry VL (-2 = not looked up)
uint64_t g_default_mask = ~(uint64_t) 0;   // fault mask the two caches were filled for
// Decision delay and the count of hops by offered outputs (parameters decision_delay, hop_stats; off by default).
int g_decision_delay = 0;
bool g_hop_stats = false;
unsigned long g_hops[2][2] = {{0, 0}, {0, 0}};    // [0 chiplet, 1 interposer][1 = more than one output offered]
// DEFT_FAST (v21; -sel DEFT_FAST, -deft_lb fast_ql). See selectFast.
bool g_fast_on = false;
bool g_fast_ql = false;
double g_fast_tick = -1.0;
std::vector<double> g_ff_next, g_ff_used;   // w f + beta b, [(router * 6 + dir) * 2 + vc]: of the cycle before / two before the use
std::deque<std::vector<double> > g_ff_mid;  // fast_stale K: K more cycles, for a decision whose costs are registered K cycles before the choice
int g_fast_stale = 0;
std::vector<double> g_fl_used;              // L per router: minimum over its outputs, one cycle older than g_ff_used
std::vector<float> g_fast_rom;              // [(router * chiplet routers + dst) * 16 + slot mask], < 0 = not filled yet
std::vector<unsigned char> g_fast_hub_ok;   // router has a functional VL
struct FastUpdate { double at; size_t index; double goal; };
std::deque<FastUpdate> g_fast_updates;      // Eq. (2) writes, applied FAST_Q_WRITE_DELAY cycles later
const double FAST_Q_WRITE_DELAY = 3.0;
unsigned long g_fast_offered[2][7] = {{0}, {0}};    // decisions by layer and number of offered outputs
// Optional VC usage file (parameter vc_stats); empty = off (default).
std::string g_vc_stats_file;
double g_vs_rc_wait_sum = 0.0;           // measured window: permission wait of outbound packets
unsigned long g_vs_rc_wait_n = 0;

// Bounded-deviation entry (parameters entry_bound_mode, entry_bound_k): applied once at
// injection to the entry candidate mask. Off by default.
enum EntryBoundMode { EB_OFF = 0, EB_MIN, EB_LUT };
int g_entry_bound_mode = EB_OFF;
int g_entry_bound_k = 0;
unsigned long g_eb_packets = 0;          // measured inter-chiplet packets bounded
double g_eb_before_sum = 0, g_eb_after_sum = 0;
unsigned long g_eb_lut_fallbacks = 0;    // mode lut with no functional LUT entry (all packets)

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
// v16: Q-table entry width (ql_bits B > 0: signed fixed point, B bits with ql_frac F fractional bits, saturating,
// round-to-nearest on every update; 0 = float32 as before) and the residual range (ql_range 1). Off by default.
int g_ql_bits = 0;
int g_ql_frac = 0;
bool g_ql_range = false;
double g_r_min = 0.0, g_r_max = 0.0;
unsigned long g_ql_changed = 0;      // updates that changed the stored value
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
    if (tm == TM_YX)    // v24: the mirror of XY
        return !((last == DIRECTION_EAST || last == DIRECTION_WEST) &&
                 (next == DIRECTION_NORTH || next == DIRECTION_SOUTH));
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
// sized 3 x W x H x 5 x W x H on first use (W, H = footprint; tm = XY, OE or YX)
std::vector<unsigned char> g_reach;

bool reach(int tm, int x, int y, int last, int tx, int ty)
{
    if (x == tx && y == ty)
        return true;
    if (g_reach.empty())
        g_reach.assign((size_t) 3 * W * H * 5 * W * H, 0);
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

// Functional VL of the mask nearest (footprint Manhattan) to router r; ties: lowest VL id.
int nearestMember(VlMask mask, int r)
{
    int best = -1, best_d = 1 << 20;
    for (int v = 0; v < NVL; v++) {
        if (!(mask & bit(v)))
            continue;
        const int d = manhattanXY(footprintX(r), footprintY(r), vlChipX(v), vlChipY(v));
        if (d < best_d) {
            best_d = d;
            best = v;
        }
    }
    return best;
}

// Uniform member of the mask from the separate RNG stream (seeded once from the run seed).
int ranMember(VlMask mask)
{
    if (!g_ran_seeded) {
        g_ran_rng.seed((unsigned int) GlobalParams::rnd_generator_seed);
        g_ran_seeded = true;
    }
    std::vector<int> members;
    for (int v = 0; v < NVL; v++)
        if (mask & bit(v))
            members.push_back(v);
    std::uniform_int_distribution<int> pick(0, (int) members.size() - 1);
    return members[pick(g_ran_rng)];
}

// MTR: the VL of the router's chiplet in the slot given by the table entry of its local position.
int mtrMember(int r, const std::vector<int> &table, const char *which)
{
    const int lx = footprintX(r) % DeftTopology::ChipletLocalWidth;
    const int ly = footprintY(r) % DeftTopology::ChipletLocalHeight;
    const int slot = table[ly * DeftTopology::ChipletLocalWidth + lx];
    std::vector<DeftTopology::VerticalLinkInfo> links =
        DeftTopology::functionalVerticalLinksForChiplet(chipletOf(r));
    for (size_t i = 0; i < links.size(); i++)
        if ((int) links[i].slot == slot)
            return links[i].vl_id;
    std::cerr << "DEFT_LB: MTR " << which << " VL (slot " << slot << ") of router " << r
              << " is faulty; MTR is evaluated fault-free only" << std::endl;
    exit(1);
}

bool loadMtrTable(const std::string &path, std::string *error_message)
{
    try {
        YAML::Node root = YAML::LoadFile(path);
        const int n = DeftTopology::ChipletLocalWidth * DeftTopology::ChipletLocalHeight;
        g_mtr_out.clear();
        g_mtr_in.clear();
        for (size_t i = 0; i < root["outbound"].size(); i++)
            g_mtr_out.push_back(root["outbound"][i].as<int>());
        for (size_t i = 0; i < root["inbound"].size(); i++)
            g_mtr_in.push_back(root["inbound"][i].as<int>());
        if ((int) g_mtr_out.size() != n || (int) g_mtr_in.size() != n) {
            if (error_message) *error_message = "mtr_table: outbound/inbound must have one entry per chiplet router";
            return false;
        }
    } catch (const std::exception &e) {
        if (error_message) *error_message = std::string("mtr_table: ") + e.what();
        return false;
    }
    return true;
}

bool parsePolicy(const std::string &v, InjectionPolicy *p)
{
    if (v == "late") *p = POLICY_LATE;
    else if (v == "lut") *p = POLICY_LUT;
    else if (v == "random") *p = POLICY_RANDOM;
    else if (v == "mindist") *p = POLICY_MINDIST;
    else if (v == "oracle") *p = POLICY_ORACLE;
    else if (v == "near") *p = POLICY_NEAR;
    else if (v == "ran") *p = POLICY_RAN;
    else if (v == "mtr") *p = POLICY_MTR;
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
        if (!DeftVerticalLinkLut::lookupPair(chipletOf(src), src, chipletOf(dst), dst, &entry, &err)) {
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
    if (c.exit_policy == POLICY_NEAR)
        es = bit(nearestMember(fs, src));
    if (c.entry_policy == POLICY_NEAR)
        ed = bit(nearestMember(fd, dst));
    if (c.exit_policy == POLICY_RAN)
        es = bit(ranMember(fs));
    if (c.entry_policy == POLICY_RAN)
        ed = bit(ranMember(fd));
    if (c.exit_policy == POLICY_MTR)
        es = bit(mtrMember(src, g_mtr_out, "outbound"));
    if (c.entry_policy == POLICY_MTR)
        ed = bit(mtrMember(dst, g_mtr_in, "inbound"));

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
    case POLICY_NEAR: return "near";
    case POLICY_RAN: return "ran";
    case POLICY_MTR: return "mtr";
    }
    return "?";
}

std::string turnModelName(int tm)
{
    if (tm == TM_YX) return "YX";
    if (tm == TM_O1) return "O1";
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
        else if (value == "YX" && key == "ipos_tm") tm = TM_YX;     // v24: interposer only
        else if (value == "O1" && key == "ipos_tm") tm = TM_O1;     // v24: XY in VN0, YX in VN1; interposer only
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
    if (key == "vc_stats") {           // VC usage per link direction (v17); off by default
        g_vc_stats_file = value;
        return true;
    }
    if (key == "mtr_table") {          // MTR baseline tables (results_v10/mtr_config.json)
        g_mtr_file = value;
        return true;
    }
    if (key == "entry_bound_mode") {
        if (value == "off") g_entry_bound_mode = EB_OFF;
        else if (value == "min") g_entry_bound_mode = EB_MIN;
        else if (value == "lut") g_entry_bound_mode = EB_LUT;
        else {
            if (error_message) *error_message = "entry_bound_mode must be off, min or lut";
            return false;
        }
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
    else if (key == "ql_bits") {
        if (d < 0 || d != std::floor(d) || d == 1 || d > 32) {
            if (error_message) *error_message = "ql_bits must be 0 (float) or an integer in 2..32";
            return false;
        }
        g_ql_bits = (int) d;
    }
    else if (key == "ql_frac") {
        if (d < 0 || d != std::floor(d) || d > 31) {
            if (error_message) *error_message = "ql_frac must be an integer in 0..31";
            return false;
        }
        g_ql_frac = (int) d;
    }
    else if (key == "ql_range") {
        if (d != 0.0 && d != 1.0) {
            if (error_message) *error_message = "ql_range must be 0 or 1";
            return false;
        }
        g_ql_range = d != 0.0;
    }
    else if (key == "ql_lookahead") {
        if (d != 0.0 && d != 1.0) {
            if (error_message) *error_message = "ql_lookahead must be 0 or 1";
            return false;
        }
        g_ql_lookahead = (int) d;
    }
    else if (key == "oracle_beta") c.oracle_beta = d;
    else if (key == "vn_rules") {
        if (d != 0.0 && d != 1.0) {
            if (error_message) *error_message = "vn_rules must be 0 or 1";
            return false;
        }
        DeftVirtualNetwork::setRulesActive(d != 0.0);
    }
    else if (key == "rc") {
        if (d != 0.0 && d != 1.0) {
            if (error_message) *error_message = "rc must be 0 or 1";
            return false;
        }
        g_rc = d != 0.0;
    }
    else if (key == "rc_slots") {
        if (d < 1 || d != std::floor(d)) {
            if (error_message) *error_message = "rc_slots must be an integer >= 1";
            return false;
        }
        g_rc_slots = (int) d;
    }
    else if (key == "count_vl") {
        if (d != 0.0 && d != 1.0) {
            if (error_message) *error_message = "count_vl must be 0 or 1";
            return false;
        }
        g_count_vl = d != 0.0;
    }
    else if (key == "hop_weight_ipos") {
        if (!(d > 0)) {
            if (error_message) *error_message = "hop_weight_ipos must be > 0";
            return false;
        }
        g_hop_weight_ipos = d;
    }
    else if (key == "decision_delay") {
        if (d < 0 || d != std::floor(d)) {
            if (error_message) *error_message = "decision_delay must be an integer >= 0";
            return false;
        }
        g_decision_delay = (int) d;
    }
    else if (key == "fast_ql") {
        if (d != 0.0 && d != 1.0) {
            if (error_message) *error_message = "fast_ql must be 0 or 1";
            return false;
        }
        g_fast_ql = d != 0.0;
    }
    else if (key == "fast_stale") {
        if (d < 0 || d != std::floor(d)) {
            if (error_message) *error_message = "fast_stale must be an integer >= 0";
            return false;
        }
        g_fast_stale = (int) d;
    }
    else if (key == "hop_stats") {
        if (d != 0.0 && d != 1.0) {
            if (error_message) *error_message = "hop_stats must be 0 or 1";
            return false;
        }
        g_hop_stats = d != 0.0;
    }
    else if (key == "lookahead_route") {
        if (d != 0.0 && d != 1.0) {
            if (error_message) *error_message = "lookahead_route must be 0 or 1";
            return false;
        }
        g_lookahead_route = (int) d;
    }
    else if (key == "hysteresis") {
        if (d < 0) {
            if (error_message) *error_message = "hysteresis must be >= 0";
            return false;
        }
        g_hysteresis = d;
    }
    else if (key == "lut_bias") {
        if (d < 0) {
            if (error_message) *error_message = "lut_bias must be >= 0";
            return false;
        }
        g_lut_bias = d;
    }
    else if (key == "lookahead_fallback") {
        if (d != 0.0 && d != 1.0) {
            if (error_message) *error_message = "lookahead_fallback must be 0 or 1";
            return false;
        }
        g_lookahead_fallback = (int) d;
    }
    else if (key == "busy_state") {
        if (d != 0.0 && d != 1.0) {
            if (error_message) *error_message = "busy_state must be 0 or 1";
            return false;
        }
        g_busy_state = (int) d;
    }
    else if (key == "entry_bound_k") {
        if (d < 0 || d != std::floor(d)) {
            if (error_message) *error_message = "entry_bound_k must be an integer >= 0";
            return false;
        }
        g_entry_bound_k = (int) d;
    }
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
    return isActive() && (GlobalParams::selection_strategy == "DEFT_QL" || (g_fast_on && g_fast_ql));
}

bool fastActive()
{
    return g_fast_on;
}

bool validateConfiguration(std::string *error_message)
{
    const Config &c = g_config;
    g_fast_on = isActive() && GlobalParams::selection_strategy == "DEFT_FAST";
    if (g_fast_ql && !g_fast_on) {
        if (error_message) *error_message = "fast_ql requires -sel DEFT_FAST";
        return false;
    }
    if (g_fast_on && g_fast_ql && c.ql_key != 1) {
        if (error_message) *error_message = "fast_ql is keyed by the destination chiplet: use ql_key 1";
        return false;
    }
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
    if ((c.exit_policy == POLICY_MTR || c.entry_policy == POLICY_MTR) &&
        !loadMtrTable(g_mtr_file, error_message))
        return false;
    if (g_rc && (c.exit_policy != POLICY_NEAR && c.exit_policy != POLICY_MTR &&
                 c.exit_policy != POLICY_LUT)) {
        if (error_message) *error_message = "rc requires a deterministic exit policy (near, mtr or lut)";
        return false;
    }
    if (g_rc && DeftVirtualNetwork::rulesActive()) {
        if (error_message) *error_message = "rc is the RC baseline: use it with vn_rules 0";
        return false;
    }
    if (g_entry_bound_mode == EB_LUT && !DeftVerticalLinkLut::isLoaded()) {
        if (error_message)
            *error_message = "entry_bound_mode lut requires -deft_vl_lut";
        return false;
    }
    if (c.exit_policy == POLICY_LATE && c.chip_tm != TM_OE && c.chip_tm != TM_XY) {
        if (error_message) *error_message = "bad chiplet turn model";
        return false;
    }
    // v24
    if (c.ipos_tm == TM_O1 && !DeftVirtualNetwork::rulesActive()) {
        if (error_message) *error_message = "ipos_tm O1 takes the interposer order from the packet's VN: it needs the DeFT VN rules (vn_rules 1)";
        return false;
    }
    if ((c.ipos_tm == TM_O1 || c.ipos_tm == TM_YX) && g_fast_on) {
        if (error_message) *error_message = "ipos_tm YX / O1 is not supported by -sel DEFT_FAST";
        return false;
    }
    if (g_lut_bias > 0 && (!DeftVerticalLinkLut::isLoaded() || !DeftVerticalLinkLut::hasDestinationEntries())) {
        if (error_message) *error_message = "lut_bias needs -deft_vl_lut with entries_by_destination (the default VL is DeFT-P's choice)";
        return false;
    }
    if (g_lut_bias > 0 && g_fast_on) {
        if (error_message) *error_message = "lut_bias is not supported by -sel DEFT_FAST";
        return false;
    }
    if (g_lookahead_fallback && !g_lookahead_route) {
        if (error_message) *error_message = "lookahead_fallback requires lookahead_route 1";
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
    } else if (tm == TM_YX) {
        int ym = prod & ((1 << DIRECTION_NORTH) | (1 << DIRECTION_SOUTH));
        if (ym)
            prod = ym;
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

// Turn model of the interposer hops of a packet in virtual network vn. With ipos_tm O1 (v24) a VN0 packet is routed XY and a
// VN1 packet YX; the VN of a packet does not change on the interposer. Used wherever the interposer turn model is used:
// the offered moves, reach (through movesMask), the pruning in nextMasks and, through those, the one-hop lookahead.
int iposTm(int vn)
{
    if (g_config.ipos_tm != TM_O1)
        return g_config.ipos_tm;
    return vn == DeftVirtualNetwork::VN1 ? TM_YX : TM_XY;
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
        m = movesTowardsMask(iposTm(rd.vc_id), cur, last, cand, here);
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
               VlMask *next_exit, VlMask *next_entry, int vn)
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
        const int tm = ph == PH_SOURCE ? g_config.chip_tm : iposTm(vn);
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

// Static remaining-path length used by the selection (DEFT_HEUR, DEFT_QL, their lookahead):
// towards the best remaining candidate, each horizontal interposer hop counts g_hop_weight_ipos
// (parameter hop_weight_ipos, default 1), each chiplet hop and each VL hop 1. With the default
// weight every value is the integer hop count. The routing relation is not affected.
double remainingHops(int cur, int src, int dst, VlMask exit_mask, VlMask entry_mask)
{
    const double g = g_hop_weight_ipos;
    switch (phaseOf(cur, src, dst)) {
    case PH_INTRA:
    case PH_DEST:
        return manhattan(cur, dst);
    case PH_IPOS: {
        double best = 1 << 20;
        for (int e = 0; e < NVL; e++)
            if (entry_mask & bit(e))
                best = std::min(best, g * manhattanXY(footprintX(cur), footprintY(cur), vlChipX(e), vlChipY(e)) + 1 +
                                          manhattanXY(vlChipX(e), vlChipY(e), footprintX(dst), footprintY(dst)));
        return best;
    }
    case PH_SOURCE: {
        double best = 1 << 20;
        for (int v = 0; v < NVL; v++) {
            if (!(exit_mask & bit(v)))
                continue;
            for (int e = 0; e < NVL; e++) {
                if (!(entry_mask & bit(e)))
                    continue;
                double h = manhattanXY(footprintX(cur), footprintY(cur), vlChipX(v), vlChipY(v)) + 1 +
                           g * manhattanXY(vlChipX(v), vlChipY(v), vlChipX(e), vlChipY(e)) + 1 +
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

double hopsAfterMove(const RouteData &rd, int out_dir)
{
    const int n = neighborId(rd.current_id, out_dir);
    if (n < 0)
        return 1 << 20;
    VlMask ne, nn;
    nextMasks(rd.current_id, rd.dir_in, out_dir, rd.src_id, rd.dst_id,
              rd.deft_exit_mask, rd.deft_entry_mask, &ne, &nn, rd.vc_id);
    // the move itself: a horizontal interposer hop weighs hop_weight_ipos
    const double w = isInterposer(rd.current_id) && out_dir != DIRECTION_HUB ? g_hop_weight_ipos : 1.0;
    return w + remainingHops(n, rd.src_id, rd.dst_id, ne, nn);
}

RouteData nextRouteData(const RouteData &rd, int out_dir, int out_vc)
{
    RouteData n = rd;
    n.current_id = neighborId(rd.current_id, out_dir);
    n.dir_in = arrivalPort(out_dir);
    n.vc_id = out_vc;
    nextMasks(rd.current_id, rd.dir_in, out_dir, rd.src_id, rd.dst_id,
              rd.deft_exit_mask, rd.deft_entry_mask,
              &n.deft_exit_mask, &n.deft_entry_mask, rd.vc_id);
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

int decisionDelay()
{
    return g_decision_delay;
}

bool mustWaitDecision(const RouteData &rd, double front_cycle, double now)
{
    if (!isActive() || now >= front_cycle + g_decision_delay || rd.current_id == rd.dst_id)
        return false;
    std::vector<int> dirs;
    legalOutputsWithVn(rd, &dirs);
    return dirs.size() > 1;
}

// ---- injection ----
namespace {

// Length of the shortest turn-legal path src -> exit v -> entry e -> dst (both VL hops
// included). Each phase routes minimally under its turn model from a fresh start
// (an injected or vertically arrived head has no previous move).
int pathLength(int src, int v, int e, int dst)
{
    const int sx = footprintX(src), sy = footprintY(src);
    const int vx = vlChipX(v), vy = vlChipY(v), ex = vlChipX(e), ey = vlChipY(e);
    const int dx = footprintX(dst), dy = footprintY(dst);
    // ipos_tm O1: either order reaches every node from a fresh start, so XY stands for both
    if (!reach(g_config.chip_tm, sx, sy, DIR_NONE, vx, vy) ||
        !reach(g_config.ipos_tm == TM_O1 ? (int) TM_XY : g_config.ipos_tm, vx, vy, DIR_NONE, ex, ey) ||
        !reach(g_config.chip_tm, ex, ey, DIR_NONE, dx, dy))
        return 1 << 20;
    return manhattanXY(sx, sy, vx, vy) + 1 + manhattanXY(vx, vy, ex, ey) + 1 + manhattanXY(ex, ey, dx, dy);
}

// Bounded-deviation entry: keeps the entry candidates e with L(e) <= L_ref + k, where
// L(e) uses the best exit of exit_mask and L_ref is min_e L(e) (mode min) or L(e_LUT)
// (mode lut; e_LUT is always kept). The result is a non-empty subset of entry_mask.
VlMask boundEntryMask(int src, int dst, VlMask exit_mask, VlMask entry_mask)
{
    std::vector<int> len(NVL, 1 << 20);
    int lmin = 1 << 20;
    for (int e = 0; e < NVL; e++) {
        if (!(entry_mask & bit(e)))
            continue;
        for (int v = 0; v < NVL; v++)
            if (exit_mask & bit(v))
                len[e] = std::min(len[e], pathLength(src, v, e, dst));
        lmin = std::min(lmin, len[e]);
    }
    int ref = lmin;
    int e_lut = -1;
    if (g_entry_bound_mode == EB_LUT) {
        DeftVerticalLinkLut::Entry entry;
        if (DeftVerticalLinkLut::lookupPair(chipletOf(src), src, chipletOf(dst), dst, &entry, 0) &&
            (entry_mask & bit(entry.destination_entry.selected_vl_id))) {
            e_lut = entry.destination_entry.selected_vl_id;
            ref = len[e_lut];
        } else {
            g_eb_lut_fallbacks++;            // e_LUT faulty or missing: mode min with the same k
        }
    }
    VlMask out = 0;
    for (int e = 0; e < NVL; e++)
        if ((entry_mask & bit(e)) && len[e] <= ref + g_entry_bound_k)
            out |= bit(e);
    if (e_lut >= 0)
        out |= bit(e_lut);
    return out ? out : entry_mask;
}

} // namespace

void prepareHeadPacket(Packet &p, const bool *local_vc_full)
{
    if (!DeftVirtualNetwork::isEnabled())
        return;
    VlMask exit_mask = 0, entry_mask = 0;
    if (isActive() && chipletOf(p.src_id) >= 0 && chipletOf(p.dst_id) >= 0 &&
        chipletOf(p.src_id) != chipletOf(p.dst_id)) {
        chooseMasks(p.src_id, p.dst_id, &exit_mask, &entry_mask);
        if (g_entry_bound_mode != EB_OFF) {
            const VlMask before = entry_mask;
            entry_mask = boundEntryMask(p.src_id, p.dst_id, exit_mask, entry_mask);
            const double now = sc_time_stamp().to_double() / GlobalParams::clock_period_ps;
            if (now - GlobalParams::reset_time >= GlobalParams::stats_warm_up_time) {
                g_eb_packets++;
                g_eb_before_sum += __builtin_popcountll(before);
                g_eb_after_sum += __builtin_popcountll(entry_mask);
            }
        }
    }
    p.deft_exit_mask = exit_mask;
    p.deft_entry_mask = entry_mask;
    if (DeftVirtualNetwork::rulesActive())
        p.vc_id = DeftVirtualNetwork::assignSourceVirtualNetwork(p.src_id, p.dst_id, exit_mask, local_vc_full);
    // VN rules off (MTR, RC): the packet keeps the VC drawn by the PE, as in Noxim.
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
            if (DeftVerticalLinkLut::lookupPair(chipletOf(src), src, chipletOf(dst), dst, &e, 0)) {
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

    if ((g_hop_stats || g_decision_delay > 0) && now - GlobalParams::reset_time >= GlobalParams::stats_warm_up_time) {
        std::vector<int> offered;
        legalOutputsWithVn(rd, &offered);
        g_hops[isInterposer(cur) ? 1 : 0][offered.size() > 1 ? 1 : 0]++;
    }

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
    // v24 B2: the head leaves through another output than the one stored for this router
    if (g_lookahead_fallback && flit->deft_lookahead_out >= 0 && flit->deft_lookahead_out != out_dir)
        g_fb_taken++;
    // v23 B2: the next router's decision, from its state now, travels in the head
    flit->deft_lookahead_out = (g_lookahead_route && nrd.current_id >= 0 && nrd.current_id != rd.dst_id) ?
                               precomputeNextDecision(nrd) : -1;
}

bool lookaheadRoute()
{
    return g_lookahead_route != 0 && isActive();
}

// The decision the next router would take now for this head: its offered outputs after the move, and the active
// selection applied with that router's state. The selection counters are restored: the decision is counted where it is used.
int precomputeNextDecision(const RouteData &nrd)
{
    std::vector<int> offered;
    legalOutputsWithVn(nrd, &offered);
    if (offered.empty())
        return -1;
    g_la_stored++;
    if (offered.size() == 1)
        return offered[0];
    Router *next = routerById(nrd.current_id);
    if (!next)
        return -1;
    const unsigned long calls = g_selection_calls, adaptive = g_adaptive_decisions;
    int choice;
    g_asking_absent = true;     // v24 B3: the head is not in the next router yet (read by outputVcBusy with busy_state 1)
    if (g_fast_on)
        choice = selectFast(next, offered, nrd);
    else if (GlobalParams::selection_strategy == "DEFT_QL")
        choice = selectQLearning(next, offered, nrd);
    else if (GlobalParams::selection_strategy == "DEFT_HEUR")
        choice = selectHeuristic(next, offered, nrd);
    else
        choice = offered[rand() % offered.size()];
    g_asking_absent = false;
    g_selection_calls = calls;
    g_adaptive_decisions = adaptive;
    return choice;
}

void onStoredDecisionUsed(int stored, int fresh, bool multi)
{
    g_la_used++;
    if (multi)
        g_la_multi++;
    if (fresh != stored)
        g_la_mismatch++;
}

bool lookaheadFallback()
{
    return g_lookahead_fallback != 0;
}

bool downstreamVcFull(int router_id, int out_dir, int out_vc)
{
    Router *n = routerById(neighborId(router_id, out_dir));
    return !n || n->buffer[arrivalPort(out_dir)][out_vc].IsFull();
}

void onFallbackCheck(bool blocked, bool other)
{
    g_fb_checks++;
    if (blocked)
        g_fb_blocked++;
    if (other)
        g_fb_requests++;
}

double hysteresis()
{
    return g_hysteresis;
}

namespace {

// v23 B4: default output = smallest remaining hop count (first in the offer order on ties); another output only if its
// cost is below the default's by more than D. Called only when D > 0, so D = 0 keeps the previous code path.
int chooseWithHysteresis(const std::vector<int> &dirs, const std::vector<double> &cost, const std::vector<double> &hops)
{
    size_t def = 0;
    for (size_t k = 1; k < dirs.size(); k++)
        if (hops[k] < hops[def] - 1e-9)
            def = k;
    double best = cost[0];
    for (size_t k = 1; k < cost.size(); k++)
        best = std::min(best, cost[k]);
    if (best < cost[def] - g_hysteresis - 1e-9)
        return pickMin(dirs, cost);
    return dirs[def];
}

} // namespace

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
    if (g_busy_state) {
        // v24 B3: read from the reservation entries of the output. The VC is busy when a packet other than the asking one
        // holds it. A reservation under the asking head's own input VC is its own only if the head is in this router (at the
        // front of that VC); when the decision is computed ahead (lookahead routing) it belongs to the packet in front of it.
        int holder_in, holder_vc;
        if (!router->reservation_table.outputVcHolder(out_dir, out_vc, &holder_in, &holder_vc))
            return false;
        return g_asking_absent || holder_in != rd.dir_in || holder_vc != rd.vc_id;
    }
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

// v24 B1 (-deft_lb lut_bias D): the default VL of a packet is DeFT-P's choice, the LUT's source_exit for the source router
// (exit) and its entries_by_destination entry for the destination router (entry), whatever -deft_lut_entry says; under faults
// the LUT's choice for the current mask. -1: no entry.
int defaultVl(bool exit_phase, int src, int dst)
{
    const uint64_t mask = DeftVerticalLinkLut::currentFaultMask();
    const int nchip = DeftTopology::ChipletCount;
    if (g_default_exit.empty() || mask != g_default_mask) {
        g_default_exit.assign((size_t) NCHIP_ROUTERS * nchip, -2);
        g_default_entry.assign(NCHIP_ROUTERS, -2);
        g_default_mask = mask;
    }
    if (exit_phase) {
        int &v = g_default_exit[(size_t) src * nchip + chipletOf(dst)];
        if (v == -2) {
            DeftVerticalLinkLut::Entry e;
            v = DeftVerticalLinkLut::lookup(chipletOf(src), src, chipletOf(dst), &e, 0) ? e.source_exit.selected_vl_id : -1;
        }
        return v;
    }
    int &v = g_default_entry[dst];
    if (v == -2) {
        DeftVerticalLinkLut::VerticalLinkSelection s;
        v = DeftVerticalLinkLut::lookupDestinationEntry(dst, &s, 0) ? s.selected_vl_id : -1;
    }
    return v;
}

// +D for an offered output whose move removes the default VL of the current phase (exit in the source chiplet, entry on the
// interposer) from the candidate mask while it is still in it. Once the default VL is gone nothing is penalised. The term
// enters the choice among the offered outputs only: not the learner's TD target and not the one-hop lookahead term. The
// candidate masks and their pruning are not touched.
double lutBias(const RouteData &rd, int out_dir)
{
    const Phase ph = phaseOf(rd.current_id, rd.src_id, rd.dst_id);
    if (ph != PH_SOURCE && ph != PH_IPOS)
        return 0.0;
    const int def = defaultVl(ph == PH_SOURCE, rd.src_id, rd.dst_id);
    const VlMask before = ph == PH_SOURCE ? rd.deft_exit_mask : rd.deft_entry_mask;
    if (def < 0 || !(before & bit(def)))
        return 0.0;
    VlMask ne, nn;
    nextMasks(rd.current_id, rd.dir_in, out_dir, rd.src_id, rd.dst_id, rd.deft_exit_mask, rd.deft_entry_mask, &ne, &nn, rd.vc_id);
    return ((ph == PH_SOURCE ? ne : nn) & bit(def)) ? 0.0 : g_lut_bias;
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

// ---- DEFT_FAST ----
size_t fastIndex(int router, int dir, int vc)
{
    return ((size_t) router * 6 + dir) * 2 + vc;
}

// LB-I has no table on chiplet routers: they offer one output.
bool fastHasTable(int router)
{
    return isInterposer(router) || g_config.exit_policy == POLICY_LATE;
}

double fastLookahead(int router, int out_dir)
{
    const int n = neighborId(router, out_dir);
    return n < 0 ? 0.0 : g_fl_used[n];
}

// Cost of output o as the decision cycle sees it: the registered terms, the ROM, and with fast_ql the residual read in the
// previous cycle (the key is known when the head is buffered; writes come later, see g_fast_updates).
double fastCost(const RouteData &rd, int out_dir)
{
    const int cur = rd.current_id;
    double c = g_ff_used[fastIndex(cur, out_dir, outputVc(rd, out_dir))] + fastHops(rd, out_dir) + fastLookahead(cur, out_dir);
    if (g_fast_ql && fastHasTable(cur)) {
        ensureQ();
        c += g_q[qIndex(cur, chipletOf(rd.dst_id), out_dir)];
    }
    return c;
}

// Static part of the learner's remote estimate; the learned residual is
// kept over it (and stored in ql_prev_static when the head is forwarded).
double remoteStatic(const RouteData &rd, int out_dir)
{
    if (g_fast_on)
        return fastHops(rd, out_dir) + fastLookahead(rd.current_id, out_dir);
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
    if (g_fast_on)
        return fastCost(rd, out_dir);
    return localCost(router, rd, out_dir, g_config.ql_w, g_config.ql_busy) +
           remoteEstimate(rd, out_dir);
}

} // namespace

// Eq. (2) on the residual of entry i
static void qApply(size_t i, double goal)
{
    const float before = g_q[i];
    g_q[i] = (float) (g_q[i] + g_config.ql_alpha * (goal - g_q[i]));
    if (g_ql_bits > 0) {
        // signed fixed point: B bits, F fractional bits; round to nearest, saturate
        const double scale = std::ldexp(1.0, g_ql_frac);
        const double qmax = std::ldexp(1.0, g_ql_bits - 1) - 1.0, qmin = -std::ldexp(1.0, g_ql_bits - 1);
        double q = std::floor(g_q[i] * scale + 0.5);
        if (q > qmax) q = qmax;
        if (q < qmin) q = qmin;
        g_q[i] = (float) (q / scale);
    }
    if (g_ql_bits > 0 || g_ql_range) {
        if (g_ql_updates == 0 || g_q[i] < g_r_min) g_r_min = g_q[i];
        if (g_ql_updates == 0 || g_q[i] > g_r_max) g_r_max = g_q[i];
        g_ql_changed += g_q[i] != before;
    }
    g_ql_updates++;
}

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
    if (g_fast_on) {
        if (fastHasTable(flit.ql_prev_router)) {
            const FastUpdate u = {now + FAST_Q_WRITE_DELAY, i, goal};
            g_fast_updates.push_back(u);
        }
        return;
    }
    qApply(i, goal);
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
        if (g_lut_bias > 0)
            c += lutBias(rd, o);
        cost[k] = c;
    }
    if (g_hysteresis > 0) {
        std::vector<double> hops(dirs.size(), 0.0);
        for (size_t k = 0; k < dirs.size(); k++)
            hops[k] = hopsAfterMove(rd, dirs[k]);
        return chooseWithHysteresis(dirs, cost, hops);
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
    for (size_t k = 0; k < dirs.size(); k++) {
        cost[k] = learnerCost(router, rd, dirs[k]);
        if (g_lut_bias > 0)     // v24 B1: in the choice only (the TD target of onHeadAtFront does not have it)
            cost[k] += lutBias(rd, dirs[k]);
    }
    if (g_hysteresis > 0) {
        std::vector<double> hops(dirs.size(), 0.0);
        for (size_t k = 0; k < dirs.size(); k++)
            hops[k] = g_fast_on ? fastHops(rd, dirs[k]) : hopsAfterMove(rd, dirs[k]);
        return chooseWithHysteresis(dirs, cost, hops);
    }
    return pickMin(dirs, cost);
}

// ---- DEFT_FAST ----
// H from the ROM. One row per (router, destination); the mask is the 4-bit slot mask of the candidates kept by the move, so a row has 16
// entries and the output is not part of the index: every kept candidate lies on a minimal path through the move, so the total through
// it does not depend on the move. A destination chiplet or intra-chiplet hop has no candidates: 1 + distance to the destination.
double fastHops(const RouteData &rd, int out_dir)
{
    const int cur = rd.current_id;
    const int dst = rd.dst_id;
    const Phase ph = phaseOf(cur, rd.src_id, dst);
    if (ph != PH_SOURCE && ph != PH_IPOS)
        return 1.0 + manhattan(neighborId(cur, out_dir), dst);
    VlMask ne, nn;
    nextMasks(cur, rd.dir_in, out_dir, rd.src_id, dst, rd.deft_exit_mask, rd.deft_entry_mask, &ne, &nn, rd.vc_id);
    const VlMask kept = ph == PH_SOURCE ? ne : nn;
    int slots = 0;
    for (int v = 0; v < NVL; v++)
        if (kept & bit(v))
            slots |= 1 << (int) DeftTopology::verticalLinkById(v)->slot;
    if (g_fast_rom.empty())
        g_fast_rom.assign((size_t) NROUTERS * NCHIP_ROUTERS * 16, -1.0f);
    const size_t row = ((size_t) cur * NCHIP_ROUTERS + dst) * 16;
    if (g_fast_rom[row + slots] < 0) {
        const double g = g_hop_weight_ipos;
        const int cx = footprintX(cur), cy = footprintY(cur), dx = footprintX(dst), dy = footprintY(dst);
        const VlMask entries = functionalMask(chipletOf(dst));
        const int chip = ph == PH_SOURCE ? chipletOf(cur) : chipletOf(dst);
        std::vector<DeftTopology::VerticalLinkInfo> slot_links = DeftTopology::verticalLinksForChiplet(chip);
        double t = 1 << 20;
        for (size_t k = 0; k < slot_links.size(); k++) {
            if (!(slots >> (int) slot_links[k].slot & 1))
                continue;
            const int c = slot_links[k].vl_id;
            double total;
            if (ph == PH_IPOS) {
                total = g * manhattanXY(cx, cy, vlChipX(c), vlChipY(c)) + 1 + manhattanXY(vlChipX(c), vlChipY(c), dx, dy);
            } else {
                double rest = 1 << 20;
                for (int e = 0; e < NVL; e++)
                    if (entries & bit(e))
                        rest = std::min(rest, g * manhattanXY(vlChipX(c), vlChipY(c), vlChipX(e), vlChipY(e)) + 1 +
                                              manhattanXY(vlChipX(e), vlChipY(e), dx, dy));
                total = manhattanXY(cx, cy, vlChipX(c), vlChipY(c)) + 1 + rest;
            }
            t = std::min(t, total);
        }
        g_fast_rom[row + slots] = (float) t;
    }
    return g_fast_rom[row + slots];
}

void fastTick(double now)
{
    if (now == g_fast_tick)
        return;
    g_fast_tick = now;
    const int VC = GlobalParams::n_virtual_channels;
    if (g_ff_used.empty()) {
        g_ff_used.assign(fastIndex(NROUTERS, 0, 0), 0.0);
        g_ff_next = g_ff_used;
        g_ff_mid.assign(g_fast_stale, g_ff_used);
        g_fl_used.assign(NROUTERS, 0.0);
        g_fast_hub_ok.assign(NROUTERS, 0);
        for (int c = 0; c < DeftTopology::ChipletCount; c++) {
            std::vector<DeftTopology::VerticalLinkInfo> ls = DeftTopology::functionalVerticalLinksForChiplet(c);
            for (size_t i = 0; i < ls.size(); i++) {
                g_fast_hub_ok[ls[i].chiplet_endpoint_router_id] = 1;
                g_fast_hub_ok[ls[i].interposer_endpoint_router_id] = 1;
            }
        }
    }
    static const int DIRS[5] = {0, 1, 2, 3, DIRECTION_HUB};
    for (int r = 0; r < NROUTERS; r++) {
        double best = std::numeric_limits<double>::max();
        for (int k = 0; k < 5; k++) {
            const int d = DIRS[k];
            if (neighborId(r, d) < 0 || (d == DIRECTION_HUB && !g_fast_hub_ok[r]))
                continue;
            for (int v = 0; v < VC; v++)
                best = std::min(best, g_ff_used[fastIndex(r, d, v)]);
        }
        g_fl_used[r] = best == std::numeric_limits<double>::max() ? 0.0 : best;
    }
    if (g_fast_stale > 0) {
        g_ff_mid.push_back(std::vector<double>());
        g_ff_mid.back().swap(g_ff_next);
        g_ff_next.swap(g_ff_used);
        g_ff_used.swap(g_ff_mid.front());
        g_ff_mid.pop_front();
    } else {
        g_ff_used.swap(g_ff_next);
    }
    TReservation probe;
    probe.input = -1;
    probe.vc = -1;
    for (int r = 0; r < NROUTERS; r++) {
        Router *router = routerById(r);
        for (int k = 0; k < 5; k++) {
            const int d = DIRS[k];
            Router *n = neighborId(r, d) < 0 || (d == DIRECTION_HUB && !g_fast_hub_ok[r]) ? 0 : routerById(neighborId(r, d));
            for (int v = 0; v < VC; v++) {
                double c = 0.0;
                if (n) {
                    probe.output_vc = v;
                    c = g_config.heur_w * n->buffer[arrivalPort(d)][v].Size();
                    if (router->reservation_table.checkReservation(probe, d) == RT_OUTVC_BUSY)
                        c += g_config.heur_busy;
                }
                g_ff_next[fastIndex(r, d, v)] = c;
            }
        }
    }
    if (!g_fast_updates.empty()) {
        ensureQ();
        while (!g_fast_updates.empty() && g_fast_updates.front().at <= now) {
            qApply(g_fast_updates.front().index, g_fast_updates.front().goal);
            g_fast_updates.pop_front();
        }
    }
}

int selectFast(Router *router, const std::vector<int> &dirs, const RouteData &rd)
{
    (void) router;
    g_selection_calls++;
    if (dirs.size() > 1)
        g_adaptive_decisions++;
    g_fast_offered[isInterposer(rd.current_id) ? 1 : 0][std::min<size_t>(dirs.size(), 6)]++;
    std::vector<double> cost(dirs.size(), 0.0);
    for (size_t k = 0; k < dirs.size(); k++)
        cost[k] = fastCost(rd, dirs[k]);
    int choice;
    if (g_hysteresis > 0) {
        std::vector<double> hops(dirs.size(), 0.0);
        for (size_t k = 0; k < dirs.size(); k++)
            hops[k] = fastHops(rd, dirs[k]);
        choice = chooseWithHysteresis(dirs, cost, hops);
    } else {
        choice = pickMin(dirs, cost);
    }
    // the selection only picks an output the relation offers
    std::vector<int> offered;
    legalOutputsWithVn(rd, &offered);
    if (std::find(offered.begin(), offered.end(), choice) == offered.end()) {
        std::cerr << "DEFT_FAST picked an output that is not offered: router " << rd.current_id << " output " << choice << std::endl;
        std::abort();
    }
    return choice;
}

// ---- RC baseline: outbound injection permission (OPIC model) ----
namespace {

void rcEnsure()
{
    if ((int) g_rc_state.size() != NROUTERS) {
        g_rc_state.assign(NROUTERS, RcState());
        g_rc_ready.assign(NROUTERS, -1.0);
        g_rc_first_request.assign(NROUTERS, -1.0);
    }
}

// Grants pending requests of boundary router br in FIFO order while slots are free. The packet may
// leave its PE max(1, d) cycles after the grant (d = hop distance PE -> boundary router).
void rcServe(int br, double now)
{
    RcState &st = g_rc_state[br];
    while (st.used < g_rc_slots && !st.queue.empty()) {
        const int pe = st.queue.front();
        st.queue.pop_front();
        st.used++;
        g_rc_grants++;
        g_rc_ready[pe] = now + std::max(1, manhattan(pe, br));
    }
}

bool rcConsume(int pe, double now)
{
    if (g_rc_ready[pe] < 0 || now < g_rc_ready[pe])
        return false;
    g_rc_wait_sum += now - g_rc_first_request[pe];
    if (!g_vc_stats_file.empty() && now - GlobalParams::reset_time >= GlobalParams::stats_warm_up_time) {
        g_vs_rc_wait_sum += now - g_rc_first_request[pe];
        g_vs_rc_wait_n++;
    }
    g_rc_ready[pe] = -1.0;
    g_rc_first_request[pe] = -1.0;
    return true;
}

} // namespace

bool rcEnabled()
{
    return g_rc && isActive();
}

int rcSlots()
{
    return g_rc_slots;
}

bool rcMayInject(const Packet &packet, double now)
{
    if (!rcEnabled())
        return true;
    const int src = packet.src_id, dst = packet.dst_id;
    if (chipletOf(src) < 0 || chipletOf(dst) < 0 || chipletOf(src) == chipletOf(dst))
        return true;                       // intra-chiplet traffic needs no permission
    rcEnsure();
    if (g_rc_ready[src] >= 0)
        return rcConsume(src, now);
    if (g_rc_first_request[src] < 0) {
        VlMask e = 0, n = 0;
        chooseMasks(src, dst, &e, &n);     // deterministic exit (near / mtr / lut)
        int v = 0;
        while (!(e >> v & 1)) v++;
        const int br = DeftTopology::chipletEndpointForVerticalLink(v);
        g_rc_first_request[src] = now;
        g_rc_state[br].queue.push_back(src);
        rcServe(br, now);
    }
    return rcConsume(src, now);
}

void rcRelease(int boundary_router_id, double now)
{
    rcEnsure();
    RcState &st = g_rc_state[boundary_router_id];
    if (st.used > 0)
        st.used--;
    rcServe(boundary_router_id, now);
}

// ---- plain DEFT VL counter ----
bool countPlainVl()
{
    return g_count_vl && !isActive();
}

void onPlainHubForward(int router_id)
{
    const int v = vlAtRouter(router_id);
    if (v < 0)
        return;
    ensureVlCounters();
    if (isInterposer(router_id)) g_vl_up[v]++;
    else g_vl_down[v]++;
}

// ---- VC usage statistics (parameter vc_stats; off by default) ----
// Observation only. A link direction is (router, output): N, E, S, W or HUB; each counter has one value per VC.
// Measured window: as all other statistics, cycles with now - reset_time >= warm-up.
namespace {

const int VS_VCS = 2;
const int VS_DIRS = DIRECTIONS + 2;

struct VcLinkStat {
    unsigned long flits[VS_VCS];        // flits forwarded on the link
    unsigned long held[VS_VCS];         // head-flit cycles: output VC held by another packet
    unsigned long nocredit[VS_VCS];     // head-flit cycles: output VC owned, downstream buffer full
    unsigned long phase[VS_VCS][4];     // flits by packet phase: source chiplet, interposer, destination chiplet, intra
    double occ_sum[VS_VCS];             // this router's input buffer [port][vc] summed over the cycles
    VcLinkStat() {
        for (int v = 0; v < VS_VCS; v++) {
            flits[v] = held[v] = nocredit[v] = 0;
            occ_sum[v] = 0.0;
            for (int p = 0; p < 4; p++)
                phase[v][p] = 0;
        }
    }
};

std::vector<VcLinkStat> g_vs;          // [router * VS_DIRS + dir]; occ_sum indexed by this router's input port
std::vector<double> g_vs_rc_flits_sum, g_vs_rc_slots_sum;
std::vector<int> g_vs_rc_peak_flits, g_vs_rc_peak_slots;

VcLinkStat &vsAt(int router, int dir)
{
    if (g_vs.empty())
        g_vs.assign((size_t) NROUTERS * VS_DIRS, VcLinkStat());
    return g_vs[(size_t) router * VS_DIRS + dir];
}

bool vsMeasuring(double now)
{
    return now - GlobalParams::reset_time >= GlobalParams::stats_warm_up_time;
}

// Footprint distance from a chiplet router to the nearest functional VL of its chiplet.
int distToNearestVl(int id)
{
    const std::vector<DeftTopology::VerticalLinkInfo> links =
        DeftTopology::functionalVerticalLinksForChiplet(chipletOf(id));
    int best = 1 << 20;
    for (size_t i = 0; i < links.size(); i++)
        best = std::min(best, manhattan(id, links[i].chiplet_endpoint_router_id));
    return best;
}

// Link classes (results_v17_vcdiag/DECISIONS.md). "" = no such link.
std::string linkClass(int r, int d)
{
    if (d == DIRECTION_HUB) {
        if (vlAtRouter(r) < 0)
            return "";
        return isInterposer(r) ? "vl_up" : "vl_down";
    }
    if (d == DIRECTION_LOCAL)
        return "";
    const int n = neighborId(r, d);
    if (n < 0)
        return "";
    if (isInterposer(r))
        return "ipos";
    if (chipletOf(n) != chipletOf(r))
        return "";
    return distToNearestVl(n) < distToNearestVl(r) ? "chip_towards" : "chip_away";
}

void writeVcStatsFile()
{
    std::ofstream o(g_vc_stats_file.c_str());
    if (!o)
        return;
    const long measured = GlobalParams::simulation_time - GlobalParams::stats_warm_up_time;
    o << "{" << std::endl << "  \"measured_cycles\": " << measured << "," << std::endl;
    if (g_rc) {
        double fl = 0, sl = 0;
        int pf = 0, ps = 0, nb = 0;
        for (size_t i = 0; i < g_vs_rc_flits_sum.size(); i++) {
            if (DeftTopology::isChipletRouter((int) i) && DeftTopology::isBoundaryRouter((int) i)) {
                nb++;
                fl += g_vs_rc_flits_sum[i];
                sl += g_vs_rc_slots_sum[i];
                pf = std::max(pf, g_vs_rc_peak_flits[i]);
                ps = std::max(ps, g_vs_rc_peak_slots[i]);
            }
        }
        const double den = (double) std::max(nb, 1) * std::max(measured, 1L);
        o << "  \"rc_buffer\": {\"boundary_routers\": " << nb << ", \"mean_flits\": " << fl / den
          << ", \"mean_slots\": " << sl / den << ", \"peak_flits\": " << pf << ", \"peak_slots\": " << ps
          << ", \"permission_wait_mean\": " << (g_vs_rc_wait_n ? g_vs_rc_wait_sum / g_vs_rc_wait_n : 0.0)
          << ", \"permission_grants\": " << g_vs_rc_wait_n << "}," << std::endl;
    }
    o << "  \"links\": [" << std::endl;
    bool first = true;
    for (int r = 0; r < NROUTERS; r++) {
        for (int d = 0; d < VS_DIRS; d++) {
            const std::string cls = linkClass(r, d);
            if (cls.empty())
                continue;
            const VcLinkStat &s = vsAt(r, d);
            const VcLinkStat &dn = vsAt(neighborId(r, d), arrivalPort(d));
            o << (first ? "" : ",\n") << "    {\"r\": " << r << ", \"d\": " << d << ", \"cls\": \"" << cls
              << "\", \"f\": [" << s.flits[0] << ", " << s.flits[1] << "], \"held\": [" << s.held[0] << ", "
              << s.held[1] << "], \"nocredit\": [" << s.nocredit[0] << ", " << s.nocredit[1] << "], \"occ\": ["
              << dn.occ_sum[0] / std::max(measured, 1L) << ", " << dn.occ_sum[1] / std::max(measured, 1L)
              << "], \"phase\": [[" << s.phase[0][0] << ", " << s.phase[0][1] << ", " << s.phase[0][2] << ", "
              << s.phase[0][3] << "], [" << s.phase[1][0] << ", " << s.phase[1][1] << ", " << s.phase[1][2] << ", "
              << s.phase[1][3] << "]]}";
            first = false;
        }
    }
    o << std::endl << "  ]" << std::endl << "}" << std::endl;
}

} // namespace

bool vcStatsOn()
{
    return !g_vc_stats_file.empty();
}

void vcStatsForward(int router_id, int out_dir, int out_vc, const Flit &flit, double now)
{
    if (!vsMeasuring(now) || out_dir == DIRECTION_LOCAL || out_vc < 0 || out_vc >= VS_VCS)
        return;
    VcLinkStat &s = vsAt(router_id, out_dir);
    s.flits[out_vc]++;
    int ph;
    const Phase p = phaseOf(router_id, flit.src_id, flit.dst_id);
    if (p == PH_SOURCE) ph = 0;
    else if (p == PH_IPOS) ph = 1;
    else if (p == PH_DEST) ph = 2;
    else ph = 3;
    s.phase[out_vc][ph]++;
}

void vcStatsWait(int router_id, int out_dir, int out_vc, bool held, double now)
{
    if (!vsMeasuring(now) || out_dir == DIRECTION_LOCAL || out_vc < 0 || out_vc >= VS_VCS)
        return;
    VcLinkStat &s = vsAt(router_id, out_dir);
    if (held)
        s.held[out_vc]++;
    else
        s.nocredit[out_vc]++;
}

void vcStatsSample(Router *router, double now)
{
    if (!vsMeasuring(now))
        return;
    for (int port = 0; port < VS_DIRS; port++) {
        VcLinkStat &s = vsAt(router->local_id, port);
        for (int vc = 0; vc < VS_VCS && vc < GlobalParams::n_virtual_channels; vc++)
            s.occ_sum[vc] += router->buffer[port][vc].Size();
    }
}

void vcStatsRcSample(int router_id, int flits, int slots, double now)
{
    if (!vsMeasuring(now))
        return;
    if ((int) g_vs_rc_flits_sum.size() != NROUTERS) {
        g_vs_rc_flits_sum.assign(NROUTERS, 0.0);
        g_vs_rc_slots_sum.assign(NROUTERS, 0.0);
        g_vs_rc_peak_flits.assign(NROUTERS, 0);
        g_vs_rc_peak_slots.assign(NROUTERS, 0);
    }
    g_vs_rc_flits_sum[router_id] += flits;
    g_vs_rc_slots_sum[router_id] += slots;
    g_vs_rc_peak_flits[router_id] = std::max(g_vs_rc_peak_flits[router_id], flits);
    g_vs_rc_peak_slots[router_id] = std::max(g_vs_rc_peak_slots[router_id], slots);
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
    if (NetraceDriver::active())             // fields only present in Netrace mode
        NetraceDriver::writeJsonFields(out);
    if (g_rc)                                // fields only present with the RC baseline
        out << "    \"rc_slots\": " << g_rc_slots << ", \"rc_grants\": " << g_rc_grants
            << ", \"rc_permission_wait_mean\": " << (g_rc_grants ? g_rc_wait_sum / g_rc_grants : 0.0) << ","
            << std::endl;
    if (g_ql_bits > 0 || g_ql_range)        // fields only present with the v16 options
        out << "    \"ql_bits\": " << g_ql_bits << ", \"ql_frac\": " << g_ql_frac << ", \"ql_residual_min\": "
            << g_r_min << ", \"ql_residual_max\": " << g_r_max << ", \"ql_updates_changed\": " << g_ql_changed
            << "," << std::endl;
    if (DeftVirtualNetwork::roundRobinActive())  // field only present with -deft_vn_rr 1
        out << "    \"vn_rr\": 1," << std::endl;
    if (g_fast_on) {    // fields only present with -sel DEFT_FAST
        out << "    \"fast_offered_chip\": [";
        for (int n = 0; n < 7; n++) out << g_fast_offered[0][n] << (n < 6 ? ", " : "");
        out << "], \"fast_offered_ipos\": [";
        for (int n = 0; n < 7; n++) out << g_fast_offered[1][n] << (n < 6 ? ", " : "");
        out << "],\n";
    }
    if (g_lookahead_route)                   // fields only present with -deft_lb lookahead_route 1 (v23)
        out << "    \"lookahead_stored\": " << g_la_stored << ", \"lookahead_used\": " << g_la_used
            << ", \"lookahead_mismatch\": " << g_la_mismatch << "," << std::endl;
    if (g_hysteresis > 0)                    // field only present with -deft_lb hysteresis D > 0 (v23)
        out << "    \"hysteresis\": " << g_hysteresis << "," << std::endl;
    if (g_lut_bias > 0)                      // fields only present with the v24 options
        out << "    \"lut_bias\": " << g_lut_bias << "," << std::endl;
    if (g_busy_state)
        out << "    \"busy_state\": 1," << std::endl;
    if (g_lookahead_fallback)
        out << "    \"lookahead_fallback\": 1, \"lookahead_multi\": " << g_la_multi << ", \"lookahead_fb_checks\": " << g_fb_checks
            << ", \"lookahead_fb_blocked\": " << g_fb_blocked << ", \"lookahead_fb_requests\": " << g_fb_requests
            << ", \"lookahead_fb_taken\": " << g_fb_taken << "," << std::endl;
    if (g_hop_stats || g_decision_delay > 0)    // fields only present with the v20 options
        out << "    \"decision_delay\": " << g_decision_delay << ", \"hops_chip\": " << g_hops[0][0] + g_hops[0][1]
            << ", \"hops_chip_multi\": " << g_hops[0][1] << ", \"hops_ipos\": " << g_hops[1][0] + g_hops[1][1]
            << ", \"hops_ipos_multi\": " << g_hops[1][1] << "," << std::endl;
    if (g_hop_weight_ipos != 1.0)            // field only present when the weight is not the default
        out << "    \"hop_weight_ipos\": " << g_hop_weight_ipos << "," << std::endl;
    if (g_entry_bound_mode != EB_OFF) {     // fields only present with the option on
        out << "    \"entry_bound_mode\": \"" << (g_entry_bound_mode == EB_MIN ? "min" : "lut")
            << "\", \"entry_bound_k\": " << g_entry_bound_k << "," << std::endl;
        out << "    \"entry_bound_packets\": " << g_eb_packets << ", \"entry_bound_lut_fallbacks\": "
            << g_eb_lut_fallbacks << "," << std::endl;
        out << "    \"entry_candidates_before_mean\": " << (g_eb_packets ? g_eb_before_sum / g_eb_packets : 0.0)
            << ", \"entry_candidates_after_mean\": " << (g_eb_packets ? g_eb_after_sum / g_eb_packets : 0.0)
            << "," << std::endl;
    }
    out << "    \"packets_intra\": " << g_delays_intra.size() << std::endl;
    out << "  }" << std::endl;
    if (statsOn())
        writeStatsFile();
    if (vcStatsOn())
        writeVcStatsFile();
}

} // namespace DeftLB
