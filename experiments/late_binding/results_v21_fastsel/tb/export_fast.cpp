// v21 F2: test vectors for the DEFT_FAST RTL, from the simulator's own fastCost, selectFast and fastTick, on real Router objects.
// It reuses the helpers of the v18 exporter, whose sc_main is renamed. Link with a build's objects except Main.o and DeftLateBinding.o.
//
// Usage: export_fast MODE SIZE SCOPE USEQ OUTFILE [NVEC]
//   MODE  sel_ipos | sel_chip | regs | fb
#define sc_main v18_export_main
#include "../../results_v18_area/rtl/tb/export_vectors.cpp"
#undef sc_main

static int randF()
{
    const int f = rand() % 5;
    return (int) (config().heur_w * f + (rand() % 2 ? config().heur_busy : 0.0));
}

static void fastSetup(bool useq)
{
    GlobalParams::selection_strategy = "DEFT_FAST";
    g_fast_on = true;
    g_fast_ql = useq;
    DeftVirtualNetwork::setRoundRobinActive(true);
    buildRouters();
    fastTick(0.0);
    ensureQ();
}

static void fastSel(const std::vector<RouteData> &all, bool ipos, long nvec)
{
    const int F = g_useq ? g_par.f : 0;
    for (long i = 0; i < nvec; i++) {
        RouteData rd = all[rand() % all.size()];
        const int cur = rd.current_id;
        const bool source = !ipos && chipletOf(rd.src_id) != chipletOf(rd.dst_id) && chipletOf(cur) == chipletOf(rd.src_id);
        if (ipos) rd.vc_id = rand() % 2;
        else if (rd.dir_in == DIRECTION_HUB) rd.vc_id = 1;
        else if (source) {
            const int here = vlAtRouter(cur);
            rd.vc_id = (rd.dir_in == DIRECTION_LOCAL && here >= 0 && rd.deft_exit_mask == bit(here)) ? rand() % 2 : 0;
        } else if (chipletOf(rd.src_id) != chipletOf(rd.dst_id)) rd.vc_id = 1;
        else rd.vc_id = rand() % 2;
        // the registered terms; the round-robin counter of this router
        if (rand() % 2)
            DeftVirtualNetwork::commitBoundaryReassignmentRoundRobin(cur);
        std::vector<int> fb(80, 0), lb(40, 0), qb(80, 0);
        const int key = chipletOf(rd.dst_id);
        for (int oi = 0; oi < 5; oi++) {
            const int o = DIRS5[oi];
            for (int v = 0; v < 2; v++) {
                const int x = randF();
                g_ff_used[fastIndex(cur, o, v)] = x;
                pack(&fb, (oi * 2 + v) * 8, 8, x);
            }
            const int nb = neighborId(cur, o);
            if (nb >= 0 && linkOk(cur, o)) {
                const int l = randF();
                g_fl_used[nb] = l;
                pack(&lb, oi * 8, 8, l);
            }
            const double qv = g_useq ? randQ() : 0.0;
            g_q[qIndex(cur, key, o)] = (float) qv;
            pack(&qb, oi * 16, 16, fx(qv));
        }
        std::vector<int> dirs;
        legalOutputsWithVn(rd, &dirs);
        long long cost[5] = {0, 0, 0, 0, 0};
        int off = 0, rr = 0;
        double vbest = std::numeric_limits<double>::max();
        for (size_t k = 0; k < dirs.size(); k++) {
            const int o = dirs[k], oi = rtlDir(o);
            const double c = fastCost(rd, o);
            cost[oi] = std::llround(c * (double) (1 << F));
            off |= 1 << oi;
            vbest = std::min(vbest, c);
        }
        // the counter as the head would see it towards Down
        RouteData probe = rd;
        probe.vc_id = 0;
        probe.dir_in = DIRECTION_NORTH;
        if (!ipos && vlAtRouter(cur) >= 0)
            rr = outputVc(probe, DIRECTION_HUB);
        const bool at_dst = cur == rd.dst_id;
        if (!at_dst && dirs.empty()) { std::cerr << "no legal output in a reachable state" << std::endl; exit(1); }
        if (!dirs.empty()) {
            const int chosen = selectFast(g_net[cur], dirs, rd);
            if (cost[rtlDir(chosen)] != std::llround(vbest * (double) (1 << F))) { std::cerr << "selection not the minimum" << std::endl; exit(1); }
        }
        fprintf(g_out, "%x %x %x %x %x %x %x %x %x %s %s %s %x %x %x %x %x %x %x %x\n",
                footprintX(cur), footprintY(cur), lastMoveFromDirIn(rd.dir_in), rd.dir_in == DIRECTION_HUB, rd.vc_id,
                footprintX(rd.dst_id), footprintY(rd.dst_id), toSlots(rd.deft_entry_mask), source ? toSlots(rd.deft_exit_mask) : 0,
                hexPad(fb).c_str(), hexPad(lb).c_str(), hexPad(qb).c_str(), rr, off,
                (unsigned) cost[0], (unsigned) cost[1], (unsigned) cost[2], (unsigned) cost[3], (unsigned) cost[4], at_dst ? 1 : 0);
    }
    std::cerr << "fast selection vectors: " << nvec << " on " << all.size() << " reachable states" << std::endl;
}

// fast_regs: f, b as fastTick measures them on real routers, and the value the router sends.
static void fastRegs(long nvec)
{
    std::vector<std::pair<TReservation, int> > res;
    double now = 1.0;
    for (long i = 0; i < nvec; i++) {
        const int cur = rand() % NROUTERS;
        randomState(cur, &res);
        fastTick(now++);    // measures this state
        fastTick(now++);    // g_ff_used holds it
        fastTick(now++);    // g_fl_used holds its minimum
        std::vector<int> fb(80, 0);
        for (int oi = 0; oi < 5; oi++)
            for (int v = 0; v < 2; v++)
                pack(&fb, (oi * 2 + v) * 8, 8, (long long) g_ff_used[fastIndex(cur, DIRS5[oi], v)]);
        const Obs ob = observe(cur);
        fprintf(g_out, "%x %x %x %s %s %s %x\n", footprintX(cur), footprintY(cur), vlAtRouter(cur) >= 0 ? 1 : 0, ob.occ_self.c_str(), ob.busy.c_str(),
                hexPad(fb).c_str(), (unsigned) (long long) g_fl_used[cur]);
        clearState(cur, &res);
    }
    std::cerr << "fast register vectors: " << nvec << std::endl;
}

// LB-I boundary router: the value of a head arriving from the interposer; chiplet routers have no table.
static void fastFb(long nvec)
{
    std::vector<DeftTopology::VerticalLinkInfo> ls = DeftTopology::verticalLinksForChiplet(0);
    for (long i = 0; i < nvec; i++) {
        const int cur = ls[rand() % ls.size()].chiplet_endpoint_router_id;
        const int dst = chipRouter(0, rand() % 4, rand() % 4);
        RouteData rd = mk(cur, chipRouter(1, 0, 0), dst, DIRECTION_HUB, 1, 0, 0);
        std::vector<int> fb(80, 0), lb(40, 0);
        for (int oi = 0; oi < 5; oi++) {
            const int o = DIRS5[oi];
            for (int v = 0; v < 2; v++) {
                const int x = randF();
                g_ff_used[fastIndex(cur, o, v)] = x;
                pack(&fb, (oi * 2 + v) * 8, 8, x);
            }
            const int nb = neighborId(cur, o);
            if (nb >= 0 && linkOk(cur, o)) {
                const int l = randF();
                g_fl_used[nb] = l;
                pack(&lb, oi * 8, 8, l);
            }
        }
        double vhere = 0.0;
        if (cur != dst) {
            std::vector<int> nd;
            legalOutputsWithVn(rd, &nd);
            if (nd.size() != 1) { std::cerr << "not XY" << std::endl; exit(1); }
            vhere = fastCost(rd, nd[0]);
        }
        const int static_in = rand() % 100;
        fprintf(g_out, "%x %x %x %x %s %s %x %x %x\n", footprintX(cur), footprintY(cur), footprintX(dst), footprintY(dst),
                hexPad(fb).c_str(), hexPad(lb).c_str(), static_in, (unsigned) fx(vhere), (unsigned) fx(1.0 + vhere - static_in));
    }
    std::cerr << "fast feedback vectors: " << nvec << std::endl;
}

extern "C" int sc_main(int argc, char *argv[])
{
    if (argc < 6) { std::cerr << "usage" << std::endl; return 2; }
    const std::string mode = argv[1], size = argv[2];
    const char scope = argv[3][0];
    const bool useq = argv[4][0] == '1';
    g_out = fopen(argv[5], "w");
    const long nvec = argc > 6 ? atol(argv[6]) : 20000;
    srand(20261103);
    setup(size, scope, useq);
    if (getenv("FAST_W"))     // the tuned weights instead of those of v10
        config().heur_w = atof(getenv("FAST_W"));
    if (getenv("FAST_BETA"))
        config().heur_busy = atof(getenv("FAST_BETA"));
    fastSetup(useq);
    if (mode == "sel_ipos")
        fastSel(bfs(startsIpos(size == "2x2" ? 0 : 8), keepAny), true, nvec);
    else if (mode == "sel_chip")
        fastSel(bfs(startsChip(0, size == "2x2" ? 0 : 8, true), keepChip0), false, nvec);
    else if (mode == "regs")
        fastRegs(nvec);
    else if (mode == "fb")
        fastFb(nvec);
    else {
        std::cerr << "bad mode" << std::endl;
        return 2;
    }
    fclose(g_out);
    return 0;
}
