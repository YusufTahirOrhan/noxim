// v18 J2: test vectors for the RTL, exported from the simulator's own code.
// This file includes src/DeftLateBinding.cpp, so it calls legalMoves, nextMasks, learnerCost, bestContinuation, remoteStatic,
// onHeadAtFront and nearestMember directly, on real Router objects (no simulation is started).
// Link with bin/build/*.o except Main.o and DeftLateBinding.o.
//
// Usage: export_vectors MODE SIZE SCOPE USEQ OUTFILE [NVEC]
//   MODE  route_ipos | route_chip | xy_chip | xy_ipos | vn | near | sel_ipos | sel_chip | qupd | fb
//   SIZE  2x2 | 3x3 | 4x4; SCOPE I (LB-I, CI_*) | F (LB-F, FULL_*); USEQ 0 | 1
#include "DeftLateBinding.cpp"

#include <cstdio>
#include <set>
#include <tuple>

using namespace DeftLB;

unsigned int drained_volume;
class NoC;
NoC *n;

struct Par { int cx; int w_shift; int beta; int f; double alpha; };

static Par params(const std::string &size, char scope)
{
    // experiments_v10.methods; alpha = the shift-add value of the RTL
    Par p;
    if (size == "2x2") { p.cx = 2; p.f = 10; if (scope == 'I') { p.w_shift = 0; p.beta = 4; p.alpha = 1.0/32 + 1.0/64; }
                         else { p.w_shift = 1; p.beta = 0; p.alpha = 1.0/128 + 1.0/512; } }
    else if (size == "3x3") { p.cx = 3; p.f = 8; if (scope == 'I') { p.w_shift = 1; p.beta = 0; p.alpha = 1.0/16 + 1.0/32; }
                         else { p.w_shift = 1; p.beta = 0; p.alpha = 1.0/64 + 1.0/256; } }
    else { p.cx = 4; p.f = 8; if (scope == 'I') { p.w_shift = 1; p.beta = 0; p.alpha = 1.0/16 + 1.0/32; }
                         else { p.w_shift = 0; p.beta = 4; p.alpha = 1.0/32 + 1.0/64; } }
    return p;
}

static std::vector<Router *> g_net;
static Par g_par;
static bool g_useq;
static FILE *g_out;

static void setup(const std::string &size, char scope, bool useq)
{
    g_par = params(size, scope);
    g_useq = useq;
    GlobalParams::topology = TOPOLOGY_DEFT_2_5D;
    GlobalParams::routing_algorithm = "DEFT_LB";
    GlobalParams::selection_strategy = useq ? "DEFT_QL" : "DEFT_HEUR";
    GlobalParams::n_virtual_channels = 2;
    GlobalParams::buffer_depth = 4;
    GlobalParams::clock_period_ps = 1000;
    std::string err;
    if (!DeftTopology::configure(g_par.cx, g_par.cx, 4, 4, &err)) { std::cerr << err << std::endl; exit(1); }
    Config &c = config();
    c.exit_policy = scope == 'I' ? POLICY_LUT : POLICY_LATE;
    c.entry_policy = POLICY_LATE;
    c.chip_tm = scope == 'I' ? TM_XY : TM_OE;
    c.ipos_tm = TM_OE;
    const double w = 1 << g_par.w_shift;
    c.heur_w = w; c.heur_busy = g_par.beta; c.heur_lookahead = 1;
    c.ql_w = w; c.ql_busy = g_par.beta; c.ql_alpha = g_par.alpha; c.ql_key = 1; c.ql_eps = 0.0;
    g_ql_lookahead = 1;
    g_hop_weight_ipos = 2.0;
    g_ql_bits = 16;
    g_ql_frac = g_par.f;
}

static void buildRouters()
{
    GlobalRoutingTable grt;
    g_net.assign(NROUTERS, (Router *) 0);
    for (int id = 0; id < NROUTERS; id++) {
        Router *r = new Router(sc_gen_unique_name("r"));
        r->configure(id, 0.0, 4, grt);
        g_net[id] = r;
    }
}

// ---- masks: VL ids <-> slot bits ----
static int slotOf(int vl) { return (int) DeftTopology::verticalLinkById(vl)->slot; }

static int toSlots(VlMask m)
{
    int s = 0;
    for (int v = 0; v < NVL; v++)
        if (m & bit(v)) s |= 1 << slotOf(v);
    return s;
}

static VlMask fromSlots(int chip, int slots)
{
    VlMask m = 0;
    std::vector<DeftTopology::VerticalLinkInfo> ls = DeftTopology::verticalLinksForChiplet(chip);
    for (size_t i = 0; i < ls.size(); i++)
        if (slots >> (int) ls[i].slot & 1) m |= bit(ls[i].vl_id);
    return m;
}

static int chipRouter(int chip, int lx, int ly)
{
    return DeftTopology::chipletRouterId(chip, lx, ly);
}

static RouteData mk(int cur, int src, int dst, int dir_in, int vc, VlMask ex, VlMask en)
{
    RouteData rd;
    rd.current_id = cur; rd.src_id = src; rd.dst_id = dst; rd.dir_in = dir_in; rd.vc_id = vc;
    rd.deft_exit_mask = ex; rd.deft_entry_mask = en;
    return rd;
}

static int rtlDir(int d) { return d == DIRECTION_HUB ? 4 : d; }

// ---- reachable states ----
typedef std::tuple<int, int, int, int, unsigned long long, unsigned long long> Key;   // cur, src, dst, dir_in, exit, entry

static std::vector<RouteData> bfs(std::vector<RouteData> start, bool (*keep)(int cur))
{
    std::set<Key> seen;
    std::vector<RouteData> all;
    std::vector<RouteData> q = start;
    while (!q.empty()) {
        RouteData rd = q.back();
        q.pop_back();
        Key k(rd.current_id, rd.src_id, rd.dst_id, rd.dir_in, rd.deft_exit_mask, rd.deft_entry_mask);
        if (!seen.insert(k).second)
            continue;
        all.push_back(rd);
        std::vector<int> dirs;
        legalMoves(rd, &dirs);
        for (size_t i = 0; i < dirs.size(); i++) {
            if (dirs[i] == DIRECTION_HUB)
                continue;
            RouteData nx = nextRouteData(rd, dirs[i], rd.vc_id);
            if (keep(nx.current_id))
                q.push_back(nx);
        }
    }
    return all;
}

static bool keepAny(int) { return true; }

// The dst only matters through its chiplet and position; the source only through its chiplet: one source per chiplet is enough.
static std::vector<RouteData> startsIpos(int limit_dst)
{
    std::vector<RouteData> s;
    const int C = DeftTopology::ChipletCount;
    for (int cd = 0; cd < C; cd++) {
        for (int lx = 0; lx < 4; lx++) for (int ly = 0; ly < 4; ly++) {
            if (limit_dst && rand() % limit_dst) continue;
            const int dst = chipRouter(cd, lx, ly);
            for (int cs = 0; cs < C; cs++) {
                if (cs == cd) continue;
                const int src = chipRouter(cs, 0, 0);
                std::vector<DeftTopology::VerticalLinkInfo> ls = DeftTopology::verticalLinksForChiplet(cs);
                for (size_t i = 0; i < ls.size(); i++)
                    for (int m = 1; m < 16; m++)
                        s.push_back(mk(ls[i].interposer_endpoint_router_id, src, dst, DIRECTION_HUB, 0, 0, fromSlots(cd, m)));
            }
        }
    }
    return s;
}

static bool keepChip0(int cur) { return chipletOf(cur) == 0; }

static std::vector<RouteData> startsChip(int chip, int limit, bool lb_full)
{
    std::vector<RouteData> s;
    const int C = DeftTopology::ChipletCount;
    const int other = chip == 0 ? 1 : 0;
    for (int lx = 0; lx < 4; lx++) for (int ly = 0; ly < 4; ly++) {
        const int a = chipRouter(chip, lx, ly);
        // source phase
        for (int cd = 0; cd < C; cd++) {
            if (cd == chip) continue;
            for (int dx = 0; dx < 4; dx++) for (int dy = 0; dy < 4; dy++) {
                if (limit && rand() % limit) continue;
                const int dst = chipRouter(cd, dx, dy);
                if (lb_full) {
                    for (int m = 1; m < 16; m++)
                        s.push_back(mk(a, a, dst, DIRECTION_LOCAL, 0, fromSlots(chip, m), fromSlots(cd, 15)));
                } else {
                    for (int sl = 0; sl < 4; sl++)
                        s.push_back(mk(a, a, dst, DIRECTION_LOCAL, 0, fromSlots(chip, 1 << sl), fromSlots(cd, 15)));
                }
            }
        }
        // intra-chiplet
        for (int dx = 0; dx < 4; dx++) for (int dy = 0; dy < 4; dy++) {
            const int dst = chipRouter(chip, dx, dy);
            if (dst != a)
                s.push_back(mk(a, a, dst, DIRECTION_LOCAL, 0, 0, 0));
        }
        // destination phase: arrival on the Hub port of each boundary router
        std::vector<DeftTopology::VerticalLinkInfo> ls = DeftTopology::verticalLinksForChiplet(chip);
        for (size_t i = 0; i < ls.size(); i++)
            s.push_back(mk(ls[i].chiplet_endpoint_router_id, chipRouter(other, 0, 0), a, DIRECTION_HUB, 1, 0, 0));
    }
    return s;
}

// ---- routing vectors ----
static void routeVectors(const std::vector<RouteData> &all, bool ipos)
{
    // one line per distinct input of the unit
    std::set<std::tuple<int, int, int, int, int> > seen;   // cur, last, mask, dst, phase class
    long lines = 0;
    for (size_t i = 0; i < all.size(); i++) {
        const RouteData &rd = all[i];
        const int cur = rd.current_id;
        const int last = lastMoveFromDirIn(rd.dir_in);
        const bool source = !ipos && chipletOf(rd.src_id) != chipletOf(rd.dst_id) && chipletOf(cur) == chipletOf(rd.src_id);
        const int mask = ipos ? toSlots(rd.deft_entry_mask) : (source ? toSlots(rd.deft_exit_mask) : 0);
        if (!seen.insert(std::make_tuple(cur, last, mask, rd.dst_id, source)).second)
            continue;
        std::vector<int> dirs;
        legalMoves(rd, &dirs);
        int off = 0;
        int pr[5] = {0, 0, 0, 0, 0};
        for (size_t k = 0; k < dirs.size(); k++) {
            VlMask ne, nn;
            nextMasks(cur, rd.dir_in, dirs[k], rd.src_id, rd.dst_id, rd.deft_exit_mask, rd.deft_entry_mask, &ne, &nn);
            off |= 1 << rtlDir(dirs[k]);
            pr[rtlDir(dirs[k])] = toSlots(ipos ? nn : (source ? ne : 0));
        }
        const int here = vlAtRouter(cur);
        const int has_hub = here >= 0;
        fprintf(g_out, "%x %x %x %x %x %x %x %x %x %x %x %x %x %x %x\n", footprintX(cur), footprintY(cur), last, mask,
                footprintX(rd.dst_id), footprintY(rd.dst_id), source ? 1 : 0, cur == rd.dst_id ? 1 : 0, has_hub, off,
                pr[0], pr[1], pr[2], pr[3], pr[4]);
        lines++;
    }
    std::cerr << "routing vectors: " << lines << std::endl;
}

// XY units: the DeFT relation (singleton masks, XY turn models): one output, or Local at the destination.
static void xyChip()
{
    config().chip_tm = TM_XY;
    std::vector<RouteData> all = bfs(startsChip(0, 0, false), keepChip0);
    std::set<std::tuple<int, int, int, int> > seen;
    long lines = 0;
    for (size_t i = 0; i < all.size(); i++) {
        const RouteData &rd = all[i];
        const bool source = chipletOf(rd.src_id) != chipletOf(rd.dst_id) && chipletOf(rd.current_id) == chipletOf(rd.src_id);
        const int slot = source ? __builtin_ctz(toSlots(rd.deft_exit_mask)) : 0;
        if (!seen.insert(std::make_tuple(rd.current_id, rd.dst_id, source, slot)).second)
            continue;
        std::vector<int> dirs;
        legalMoves(rd, &dirs);
        const int out = rd.current_id == rd.dst_id ? DIRECTION_LOCAL : dirs.at(0);
        if (rd.current_id != rd.dst_id && dirs.size() != 1) { std::cerr << "not deterministic" << std::endl; exit(1); }
        fprintf(g_out, "%x %x %x %x %x %x %x\n", footprintX(rd.current_id), footprintY(rd.current_id), footprintX(rd.dst_id),
                footprintY(rd.dst_id), slot, vlAtRouter(rd.current_id) >= 0 ? 1 : 0, out);
        lines++;
    }
    std::cerr << "xy_chip vectors: " << lines << std::endl;
}

static void xyIpos()
{
    config().ipos_tm = TM_XY;
    std::vector<RouteData> st;
    const int C = DeftTopology::ChipletCount;
    for (int cd = 0; cd < C; cd++)
        for (int cs = 0; cs < C; cs++) {
            if (cs == cd) continue;
            std::vector<DeftTopology::VerticalLinkInfo> ls = DeftTopology::verticalLinksForChiplet(cs);
            for (size_t i = 0; i < ls.size(); i++)
                for (int sl = 0; sl < 4; sl++)
                    st.push_back(mk(ls[i].interposer_endpoint_router_id, chipRouter(cs, 0, 0), chipRouter(cd, 0, 0), DIRECTION_HUB, 0, 0,
                                    fromSlots(cd, 1 << sl)));
        }
    std::vector<RouteData> all = bfs(st, keepAny);
    std::set<std::tuple<int, int, int, int> > seen;
    long lines = 0;
    for (size_t i = 0; i < all.size(); i++) {
        const RouteData &rd = all[i];
        const int slot = __builtin_ctz(toSlots(rd.deft_entry_mask));
        if (!seen.insert(std::make_tuple(rd.current_id, rd.dst_id, 0, slot)).second)
            continue;
        std::vector<int> dirs;
        legalMoves(rd, &dirs);
        if (dirs.size() != 1) { std::cerr << "not deterministic" << std::endl; exit(1); }
        fprintf(g_out, "%x %x %x %x %x %x %x\n", footprintX(rd.current_id), footprintY(rd.current_id), footprintX(rd.dst_id),
                footprintY(rd.dst_id), slot, vlAtRouter(rd.current_id) >= 0 ? 1 : 0, dirs[0]);
        lines++;
    }
    std::cerr << "xy_ipos vectors: " << lines << std::endl;
}

// VN rules: every (input port, output port, VC) that can occur.
static void vnVectors()
{
    long lines = 0;
    const int bcp = DeftTopology::verticalLinksForChiplet(0)[0].chiplet_endpoint_router_id;
    const int icp = DeftTopology::verticalLinksForChiplet(0)[0].interposer_endpoint_router_id;
    for (int layer = 0; layer < 2; layer++)
        for (int in = 0; in < 6; in++)
            for (int out = 0; out < 6; out++)
                for (int vc = 0; vc < 2; vc++) {
                    if (out == DIRECTION_LOCAL && layer == 1) continue;
                    if (in == DIRECTION_LOCAL && layer == 1) continue;
                    if (in == out && in != DIRECTION_LOCAL) continue;           // no U-turn
                    if (in == DIRECTION_LOCAL && out == DIRECTION_LOCAL) continue;
                    RouteData rd = mk(layer ? icp : bcp, 0, 0, in, vc, 0, 0);
                    const int ovc = DeftVirtualNetwork::selectOutputVirtualNetwork(rd, out, 0);
                    const int ok = DeftVirtualNetwork::isOutputDirectionAllowed(rd, out);
                    fprintf(g_out, "%x %x %x %x %x %x\n", layer, in, out, vc, ovc, ok);
                    lines++;
                }
    std::cerr << "vn vectors: " << lines << std::endl;
}

static void nearVectors()
{
    long lines = 0;
    for (int lx = 0; lx < 4; lx++) for (int ly = 0; ly < 4; ly++)
        for (int m = 1; m < 16; m++) {
            const int v = nearestMember(fromSlots(0, m), chipRouter(0, lx, ly));
            fprintf(g_out, "%x %x %x %x\n", lx, ly, m, slotOf(v));
            lines++;
        }
    std::cerr << "near vectors: " << lines << std::endl;
}

// ---- selection state ----
static void setBuf(int router, int port, int vc, int k)
{
    Buffer &b = g_net[router]->buffer[port][vc];
    while (b.Size() > 0) b.Pop();
    Flit f = Flit();
    for (int i = 0; i < k; i++) b.Push(f);
}

static bool linkOk(int r, int d)
{
    if (d == DIRECTION_HUB) return vlAtRouter(r) >= 0;
    const int nb = neighborId(r, d);
    if (nb < 0) return false;
    if (!isInterposer(r) && chipletOf(nb) != chipletOf(r)) return false;
    return true;
}

static const int DIRS5[5] = {DIRECTION_NORTH, DIRECTION_EAST, DIRECTION_SOUTH, DIRECTION_WEST, DIRECTION_HUB};

// Random occupancies behind every output of cur and of its neighbours; random busy output VCs at cur.
static void randomState(int cur, std::vector<std::pair<TReservation, int> > *res)
{
    for (int oi = 0; oi < 5; oi++) {
        const int o = DIRS5[oi];
        if (!linkOk(cur, o)) continue;
        const int nb = neighborId(cur, o);
        for (int v = 0; v < 2; v++) setBuf(nb, arrivalPort(o), v, rand() % 5);
        for (int zi = 0; zi < 5; zi++) {
            const int z = DIRS5[zi];
            if (!linkOk(nb, z)) continue;
            const int nn = neighborId(nb, z);
            for (int v = 0; v < 2; v++) setBuf(nn, arrivalPort(z), v, rand() % 5);
        }
        for (int v = 0; v < 2; v++)
            if (rand() % 2) {
                TReservation r;
                r.input = 100 + oi * 2 + v;
                r.vc = v;
                r.output_vc = v;
                g_net[cur]->reservation_table.reserve(r, o);
                res->push_back(std::make_pair(r, o));
            }
    }
}

static void clearState(int cur, std::vector<std::pair<TReservation, int> > *res)
{
    for (size_t i = 0; i < res->size(); i++)
        g_net[cur]->reservation_table.release((*res)[i].first, (*res)[i].second);
    res->clear();
}

// Bits to a hex token.
static std::string hexOf(const std::vector<int> &bits)
{
    std::string s;
    for (int i = (int) bits.size() - 1; i >= 0; i -= 4) {
        int d = 0;
        for (int k = 0; k < 4; k++) {
            const int j = i - k;
            d = d * 2 + (j >= 0 ? bits[j] : 0);
        }
        // align: the top digit may be short, handled by shifting below
        s += "0123456789abcdef"[d];
    }
    return s;
}

static void pack(std::vector<int> *bits, int lsb, int width, long long v)
{
    for (int i = 0; i < width; i++) (*bits)[lsb + i] = (v >> i) & 1;
}

// The hex of a vector whose length is a multiple of 4 is exact; pad to a multiple of 4 before calling hexOf.
static std::string hexPad(std::vector<int> bits)
{
    while (bits.size() % 4) bits.push_back(0);
    return hexOf(bits);
}

struct Obs { std::string occ_self, busy, occ_nb; };

static Obs observe(int cur)
{
    std::vector<int> a(30, 0), b(10, 0), c(150, 0);
    for (int oi = 0; oi < 5; oi++) {
        const int o = DIRS5[oi];
        if (!linkOk(cur, o)) continue;
        const int nb = neighborId(cur, o);
        for (int v = 0; v < 2; v++) {
            pack(&a, (oi * 2 + v) * 3, 3, g_net[nb]->buffer[arrivalPort(o)][v].Size());
            TReservation r;
            r.input = 99;
            r.vc = 0;
            r.output_vc = v;
            b[oi * 2 + v] = g_net[cur]->reservation_table.checkReservation(r, o) == RT_OUTVC_BUSY;
        }
        for (int zi = 0; zi < 5; zi++) {
            const int z = DIRS5[zi];
            if (!linkOk(nb, z)) continue;
            const int nn = neighborId(nb, z);
            for (int v = 0; v < 2; v++)
                pack(&c, (oi * 5 + zi) * 6 + v * 3, 3, g_net[nn]->buffer[arrivalPort(z)][v].Size());
        }
    }
    Obs ob;
    ob.occ_self = hexPad(a);
    ob.busy = hexPad(b);
    ob.occ_nb = hexPad(c);
    return ob;
}

static long long fx(double v) { return std::llround(v * (double) (1 << g_par.f)); }

static double randQ()
{
    // full 16-bit range is exercised; most values near the residuals seen in the runs
    const int r = rand() % 8;
    long long q;
    if (r == 0) q = (long long) (rand() % 65536) - 32768;
    else q = (long long) (rand() % (64 << g_par.f)) - (32 << g_par.f);
    return (double) q / (double) (1 << g_par.f);
}

static void selVectors(const std::vector<RouteData> &all, bool ipos, long nvec)
{
    ensureQ();
    std::vector<std::pair<TReservation, int> > res;
    const int F = g_useq ? g_par.f : 0;
    for (long i = 0; i < nvec; i++) {
        RouteData rd = all[rand() % all.size()];
        const int cur = rd.current_id;
        const bool source = !ipos && chipletOf(rd.src_id) != chipletOf(rd.dst_id) && chipletOf(cur) == chipletOf(rd.src_id);
        // a VC the head can have
        if (ipos) rd.vc_id = rand() % 2;
        else if (rd.dir_in == DIRECTION_HUB) rd.vc_id = 1;
        else if (source) {
            const int here = vlAtRouter(cur);
            rd.vc_id = (rd.dir_in == DIRECTION_LOCAL && here >= 0 && rd.deft_exit_mask == bit(here)) ? rand() % 2 : 0;
        } else if (chipletOf(rd.src_id) != chipletOf(rd.dst_id)) rd.vc_id = 1;
        else rd.vc_id = rand() % 2;
        randomState(cur, &res);
        std::vector<int> qb(80, 0);
        const int key = chipletOf(rd.dst_id);
        for (int oi = 0; oi < 5; oi++) {
            const double qv = g_useq ? randQ() : 0.0;
            g_q[qIndex(cur, key, DIRS5[oi])] = (float) qv;
            pack(&qb, oi * 16, 16, fx(qv));
        }
        const int static_in = rand() % 100;
        std::vector<int> dirs;
        legalOutputsWithVn(rd, &dirs);
        long long cost[5] = {0, 0, 0, 0, 0};
        long long st[5] = {0, 0, 0, 0, 0};
        int off = 0;
        double vbest = std::numeric_limits<double>::max();
        Router *router = g_net[cur];
        for (size_t k = 0; k < dirs.size(); k++) {
            const int o = dirs[k], oi = rtlDir(o);
            double c;
            if (g_useq) c = learnerCost(router, rd, o);
            else c = localCost(router, rd, o, config().heur_w, config().heur_busy) + 1.0 + bestContinuation(rd, o, config().heur_w);
            const double s = remoteStatic(rd, o);
            cost[oi] = std::llround(c * (double) (1 << F));
            st[oi] = g_useq ? std::llround(s) : std::llround(1.0 + bestContinuation(rd, o, config().heur_w));
            off |= 1 << oi;
            vbest = std::min(vbest, c);
        }
        const bool at_dst = cur == rd.dst_id;
        if (!at_dst && dirs.empty()) { std::cerr << "no legal output in a reachable state" << std::endl; exit(1); }
        // the simulator's own selection must pick from the minimum
        if (!dirs.empty()) {
            const int chosen = g_useq ? selectQLearning(router, dirs, rd) : selectHeuristic(router, dirs, rd);
            if (cost[rtlDir(chosen)] != std::llround(vbest * (double) (1 << F))) { std::cerr << "selection not the minimum" << std::endl; exit(1); }
        }
        const double vhere = at_dst ? 0.0 : vbest;
        const long long goal = std::llround((1.0 + vhere - static_in) * (double) (1 << F));
        const Obs ob = observe(cur);
        fprintf(g_out, "%x %x %x %x %x %x %x %x %x %s %s %s %s %x %x %x %x %x %x %x %x %x %x %x %x %x %x %x\n",
                footprintX(cur), footprintY(cur), lastMoveFromDirIn(rd.dir_in), rd.dir_in == DIRECTION_HUB, rd.vc_id,
                footprintX(rd.dst_id), footprintY(rd.dst_id), toSlots(rd.deft_entry_mask),
                source ? toSlots(rd.deft_exit_mask) : 0,
                ob.occ_self.c_str(), ob.busy.c_str(), ob.occ_nb.c_str(), hexPad(qb).c_str(), static_in, off,
                (unsigned) cost[0], (unsigned) cost[1], (unsigned) cost[2], (unsigned) cost[3], (unsigned) cost[4],
                (unsigned) st[0], (unsigned) st[1], (unsigned) st[2], (unsigned) st[3], (unsigned) st[4],
                (unsigned) std::llround(vhere * (double) (1 << F)), (unsigned) goal, at_dst ? 1 : 0);
        clearState(cur, &res);
    }
    std::cerr << "selection vectors: " << nvec << " on " << all.size() << " reachable states" << std::endl;
}

// Eq. (2): the update in onHeadAtFront, on real routers.
static void qupdVectors(const std::vector<RouteData> &all, long nvec)
{
    ensureQ();
    std::vector<std::pair<TReservation, int> > res;
    for (long i = 0; i < nvec; i++) {
        RouteData rd = all[rand() % all.size()];
        const int cur = rd.current_id;
        rd.vc_id = 0;
        randomState(cur, &res);
        const int key = chipletOf(rd.dst_id);
        for (int oi = 0; oi < 5; oi++)
            g_q[qIndex(cur, key, DIRS5[oi])] = (float) randQ();
        // the previous router's entry: any other router, one direction
        const int prev = (cur + 1 + rand() % (NROUTERS - 1)) % NROUTERS;
        const int pdir = DIRS5[rand() % 5];
        const double before = randQ();
        const size_t qi = qIndex(prev, key, pdir);
        g_q[qi] = (float) before;
        Flit f = Flit();
        f.src_id = rd.src_id;
        f.dst_id = rd.dst_id;
        f.vc_id = rd.vc_id;
        f.deft_exit_mask = rd.deft_exit_mask;
        f.deft_entry_mask = rd.deft_entry_mask;
        f.ql_prev_router = prev;
        f.ql_prev_dir = pdir;
        f.ql_prev_static = rand() % 100;
        // the same target as onHeadAtFront computes
        double vhere = 0.0;
        if (cur != rd.dst_id) {
            std::vector<int> nd;
            legalOutputsWithVn(rd, &nd);
            vhere = std::numeric_limits<double>::max();
            for (size_t k = 0; k < nd.size(); k++)
                vhere = std::min(vhere, learnerCost(g_net[cur], rd, nd[k]));
        }
        const double goal = 1.0 + vhere - f.ql_prev_static;
        onHeadAtFront(g_net[cur], rd.dir_in, f, 0.0);
        fprintf(g_out, "%x %x %x\n", (unsigned) (fx(before) & 0xffff), (unsigned) fx(goal), (unsigned) (fx(g_q[qi]) & 0xffff));
        clearState(cur, &res);
    }
    std::cerr << "q update vectors: " << nvec << std::endl;
}

// LB-I boundary router: value of a head arriving from the interposer, no table on chiplet routers (residual 0).
static void fbVectors(long nvec)
{
    ensureQ();
    std::vector<std::pair<TReservation, int> > res;
    std::vector<DeftTopology::VerticalLinkInfo> ls = DeftTopology::verticalLinksForChiplet(0);
    for (long i = 0; i < nvec; i++) {
        const int cur = ls[rand() % ls.size()].chiplet_endpoint_router_id;
        const int dst = chipRouter(0, rand() % 4, rand() % 4);
        RouteData rd = mk(cur, chipRouter(1, 0, 0), dst, DIRECTION_HUB, 1, 0, 0);
        randomState(cur, &res);
        double vhere = 0.0;
        if (cur != dst) {
            std::vector<int> nd;
            legalOutputsWithVn(rd, &nd);
            if (nd.size() != 1) { std::cerr << "not XY" << std::endl; exit(1); }
            vhere = learnerCost(g_net[cur], rd, nd[0]);
        }
        const int static_in = rand() % 100;
        const Obs ob = observe(cur);
        fprintf(g_out, "%x %x %x %x %s %s %s %x %x %x\n", footprintX(cur), footprintY(cur), footprintX(dst), footprintY(dst),
                ob.occ_self.c_str(), ob.busy.c_str(), ob.occ_nb.c_str(), static_in, (unsigned) fx(vhere), (unsigned) fx(1.0 + vhere - static_in));
        clearState(cur, &res);
    }
    std::cerr << "fb vectors: " << nvec << std::endl;
}

int sc_main(int argc, char *argv[])
{
    if (argc < 6) { std::cerr << "usage" << std::endl; return 2; }
    const std::string mode = argv[1], size = argv[2];
    const char scope = argv[3][0];
    const bool useq = argv[4][0] == '1';
    g_out = fopen(argv[5], "w");
    const long nvec = argc > 6 ? atol(argv[6]) : 20000;
    srand(20261102);
    setup(size, scope, useq);
    if (mode == "route_ipos") {
        routeVectors(bfs(startsIpos(0), keepAny), true);
    } else if (mode == "route_chip") {
        routeVectors(bfs(startsChip(0, 0, true), keepChip0), false);
    } else if (mode == "xy_chip") {
        xyChip();
    } else if (mode == "xy_ipos") {
        xyIpos();
    } else if (mode == "vn") {
        vnVectors();
    } else if (mode == "near") {
        nearVectors();
    } else {
        buildRouters();
        if (mode == "sel_ipos") {
            selVectors(bfs(startsIpos(size == "2x2" ? 0 : 8), keepAny), true, nvec);
        } else if (mode == "sel_chip") {
            selVectors(bfs(startsChip(0, size == "2x2" ? 0 : 8, true), keepChip0), false, nvec);
        } else if (mode == "qupd") {
            qupdVectors(bfs(startsIpos(size == "2x2" ? 0 : 8), keepAny), nvec);
        } else if (mode == "fb") {
            fbVectors(nvec);
        } else {
            std::cerr << "bad mode" << std::endl;
            return 2;
        }
    }
    fclose(g_out);
    return 0;
}
