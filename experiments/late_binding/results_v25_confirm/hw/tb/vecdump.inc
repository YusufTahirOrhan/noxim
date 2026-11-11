// v25 Part F2: test vectors for the RTL, taken from simulator runs.
// This file is appended to a COPY of src/DeftLateBinding.cpp by patch_vecdump.py (the repository's sources and bin/noxim
// are not touched). With the environment variable LB25_VEC=<prefix> the instrumented simulator writes, for every routing
// evaluation at an interposer router, the inputs an RTL unit sees and the simulator's own results:
//   <prefix>.sel.txt  one line per evaluation of the selection (kind 0: the decision computed ahead for the next router,
//                     kind 1: the decision at the buffer front), and per stored decision of a hop with one offered output
//   <prefix>.fb.txt   one line per evaluation of Router::selectionFunction (the output asked at the buffer front)
// Nothing else changes: no random number is drawn, no simulator state is written. run_vectors.sh checks that the
// statistics file of an instrumented run is byte-identical to that of bin/noxim.
// All fields are hexadecimal. Directions: 0 N, 1 E, 2 S, 3 W, 4 Hub; 7 = none. Masks are slot masks of the destination chiplet.
#include <cstdio>
#include <cstdlib>

namespace DeftLB {

namespace {

FILE *g_vsel = 0, *g_vfb = 0;
bool g_vinit = false;
long g_vmax = 0, g_vn_sel = 0, g_vn_fb = 0;

void vecInit()
{
    if (g_vinit)
        return;
    g_vinit = true;
    const char *p = getenv("LB25_VEC");
    if (!p)
        return;
    const std::string s(p);
    g_vsel = fopen((s + ".sel.txt").c_str(), "w");
    g_vfb = fopen((s + ".fb.txt").c_str(), "w");
    const char *m = getenv("LB25_VEC_MAX");
    g_vmax = m ? atol(m) : 0;         // 0: no limit; else at most this many lines per file
}

int vSlot(int vl)
{
    return (int) DeftTopology::verticalLinkById(vl)->slot;
}

int vSlots(VlMask m)
{
    int s = 0;
    for (int v = 0; v < NVL; v++)
        if (m & bit(v))
            s |= 1 << vSlot(v);
    return s;
}

int vDir(int d)
{
    return d == DIRECTION_HUB ? 4 : (d >= 0 && d <= 3 ? d : 7);
}

const int V_DIRS[5] = {0, 1, 2, 3, DIRECTION_HUB};

// position, last move, VN, destination, entry mask, router has a VL
void vecHead(FILE *f, const RouteData &rd)
{
    const int cur = rd.current_id;
    fprintf(f, "%x %x %x %x %x %x %x %x", footprintX(cur), footprintY(cur), lastMoveFromDirIn(rd.dir_in), rd.vc_id,
            footprintX(rd.dst_id), footprintY(rd.dst_id), vSlots(rd.deft_entry_mask), vlAtRouter(cur) >= 0 ? 1 : 0);
}

// offered outputs and the entry mask after each of them
void vecRel(FILE *f, const RouteData &rd, const std::vector<int> &dirs)
{
    int off = 0, pr[5] = {0, 0, 0, 0, 0};
    for (size_t i = 0; i < dirs.size(); i++) {
        VlMask ne, nn;
        nextMasks(rd.current_id, rd.dir_in, dirs[i], rd.src_id, rd.dst_id, rd.deft_exit_mask, rd.deft_entry_mask, &ne, &nn, rd.vc_id);
        off |= 1 << vDir(dirs[i]);
        pr[vDir(dirs[i])] = vSlots(nn);
    }
    fprintf(f, " %x %x %x %x %x %x", off, pr[0], pr[1], pr[2], pr[3], pr[4]);
}

} // namespace

bool vecOn()
{
    vecInit();
    return g_vsel != 0;
}

// kind 0: computed ahead for the next router (lookahead routing); kind 1: at the buffer front. cost = 0: one offered output,
// no selection was evaluated.
void vecSel(int kind, Router *router, const std::vector<int> &dirs, const RouteData &rd, const std::vector<double> *cost, int choice)
{
    if (!vecOn() || !router || !isInterposer(rd.current_id) || (g_vmax && g_vn_sel >= g_vmax))
        return;
    g_vn_sel++;
    const int cur = rd.current_id;
    int def = 7;
    if (g_lut_bias > 0) {
        const int d = defaultVl(false, rd.src_id, rd.dst_id);
        if (d >= 0)
            def = vSlot(d);
    }
    fprintf(g_vsel, "%x ", kind);
    vecHead(g_vsel, rd);
    fprintf(g_vsel, " %x", def);
    // own occupancy per output on the head's VN; then, per output, the occupancy behind each output of the neighbour
    // (the head's VN on the interposer, VN1 behind the Up link)
    for (int o = 0; o < 5; o++)
        fprintf(g_vsel, " %x", (int) downstreamOccupancy(router, V_DIRS[o], rd.vc_id));
    for (int o = 0; o < 5; o++) {
        Router *nr = routerById(neighborId(cur, V_DIRS[o]));
        for (int z = 0; z < 5; z++)
            fprintf(g_vsel, " %x", nr ? (int) downstreamOccupancy(nr, V_DIRS[z], o == 4 ? (int) DeftVirtualNetwork::VN1 : rd.vc_id) : 0);
    }
    vecRel(g_vsel, rd, dirs);
    int c[5] = {0, 0, 0, 0, 0};
    if (cost)
        for (size_t k = 0; k < dirs.size(); k++)
            c[vDir(dirs[k])] = (int) std::floor((*cost)[k] + 0.5);
    fprintf(g_vsel, " %x %x %x %x %x %x %x\n", cost ? 1 : 0, c[0], c[1], c[2], c[3], c[4], vDir(choice));
}

// held_o: the output the head already holds (-1: none); free6: Router::outputFreeForHead per Noxim direction; result: what
// selectionFunction returned.
void vecFront(const RouteData &rd, int held_o, const int *free6, int result)
{
    if (!vecOn() || !isInterposer(rd.current_id) || (g_vmax && g_vn_fb >= g_vmax))
        return;
    g_vn_fb++;
    std::vector<int> dirs;
    legalOutputsWithVn(rd, &dirs);
    vecHead(g_vfb, rd);
    fprintf(g_vfb, " %x %x", (g_lookahead_route && rd.deft_lookahead_out >= 0) ? vDir(rd.deft_lookahead_out) : 7, held_o >= 0 ? vDir(held_o) : 7);
    vecRel(g_vfb, rd, dirs);
    int fr = 0;
    for (int o = 0; o < 5; o++)
        if (free6[V_DIRS[o]])
            fr |= 1 << o;
    fprintf(g_vfb, " %x %x %x\n", fr, g_lookahead_fallback ? 1 : 0, vDir(result));
}

} // namespace DeftLB
