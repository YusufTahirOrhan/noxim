// v21 F1: H of DEFT_FAST from its ROM (fastHops) against the current H (hopsAfterMove), for every input the relation can reach and
// more: all subsets of the functional candidates, every arrival port. It also measures which ROM index would be enough.
// This file includes src/DeftLateBinding.cpp, so both functions run as they do in the simulator (no simulation is started).
// Link with the objects of a build except Main.o and DeftLateBinding.o.
//
// Usage: rom_check SIZE SCOPE MASK     SIZE 2x2 | 3x3 | 4x4; SCOPE I (CI_*) | F (FULL_*); MASK faulty VLs as a hex bit mask
#include "DeftLateBinding.cpp"

#include <cstdio>
#include <unordered_map>

using namespace DeftLB;

unsigned int drained_volume;
class NoC;
NoC *n;

struct Range { float lo, hi; };
typedef std::unordered_map<unsigned long long, Range> Index;

static void note(Index &ix, unsigned long long key, float h)
{
    Index::iterator it = ix.find(key);
    if (it == ix.end()) {
        Range r = {h, h};
        ix[key] = r;
    } else {
        it->second.lo = std::min(it->second.lo, h);
        it->second.hi = std::max(it->second.hi, h);
    }
}

static void report(const char *name, const Index &ix)
{
    unsigned long bad = 0;
    float worst = 0;
    for (Index::const_iterator it = ix.begin(); it != ix.end(); ++it) {
        bad += it->second.hi > it->second.lo;
        worst = std::max(worst, it->second.hi - it->second.lo);
    }
    printf("  index %-32s entries %8lu  with more than one value %8lu (%5.1f %%)  largest spread %.0f\n", name, (unsigned long) ix.size(), bad,
           ix.empty() ? 0.0 : 100.0 * bad / ix.size(), worst);
}

static int slotsOf(VlMask m)
{
    int s = 0;
    for (int v = 0; v < NVL; v++)
        if (m & bit(v))
            s |= 1 << (int) DeftTopology::verticalLinkById(v)->slot;
    return s;
}

int sc_main(int argc, char **argv)
{
    if (argc < 4)
        return 2;
    const std::string size = argv[1];
    const char scope = argv[2][0];
    const unsigned long long faulty = strtoull(argv[3], 0, 16);
    const int cx = size[0] - '0';
    GlobalParams::topology = TOPOLOGY_DEFT_2_5D;
    GlobalParams::routing_algorithm = "DEFT_LB";
    GlobalParams::selection_strategy = "DEFT_FAST";
    GlobalParams::n_virtual_channels = 2;
    std::string err;
    if (!DeftTopology::configure(cx, cx, 4, 4, &err)) {
        std::cerr << err << std::endl;
        return 1;
    }
    Config &c = config();
    c.exit_policy = scope == 'I' ? POLICY_LUT : POLICY_LATE;
    c.entry_policy = POLICY_LATE;
    c.chip_tm = scope == 'I' ? TM_XY : TM_OE;
    c.ipos_tm = TM_OE;
    g_hop_weight_ipos = 2.0;
    g_fast_on = true;
    for (int v = 0; v < NVL && v < 64; v++)
        if (faulty >> v & 1)
            DeftTopology::setVerticalLinkFunctional(v, false);

    unsigned long inputs = 0, moves = 0, mismatches = 0, offered[2][7] = {{0}, {0}};
    Index by_o_m, by_o_m_chip, by_m_dst, by_o_dst_dest;

    const int C = DeftTopology::ChipletCount;
    auto visit = [&](int cur, int src, int dst, int dir_in, VlMask ex, VlMask en) {
        RouteData rd;
        rd.current_id = cur; rd.src_id = src; rd.dst_id = dst; rd.dir_in = dir_in; rd.vc_id = 0;
        rd.deft_exit_mask = ex; rd.deft_entry_mask = en;
        std::vector<int> dirs;
        legalMoves(rd, &dirs);
        inputs++;
        const bool ipos = isInterposer(cur);
        offered[ipos ? 1 : 0][std::min<size_t>(dirs.size(), 6)]++;
        const Phase ph = phaseOf(cur, src, dst);
        for (size_t k = 0; k < dirs.size(); k++) {
            const int o = dirs[k];
            const double a = fastHops(rd, o), b = hopsAfterMove(rd, o);
            moves++;
            if (a != b) {
                if (mismatches < 10)
                    printf("MISMATCH cur %d src %d dst %d dir_in %d exit %llx entry %llx o %d: rom %g current %g\n", cur, src, dst, dir_in,
                           (unsigned long long) ex, (unsigned long long) en, o, a, b);
                mismatches++;
            }
            const unsigned long long od = o == DIRECTION_HUB ? 4 : o;
            if (ph == PH_SOURCE || ph == PH_IPOS) {
                VlMask ne, nn;
                nextMasks(cur, dir_in, o, src, dst, ex, en, &ne, &nn);
                const unsigned long long m = slotsOf(ph == PH_SOURCE ? ne : nn);
                note(by_o_m, ((unsigned long long) cur << 8) | (od << 4) | m, (float) b);
                note(by_o_m_chip, ((unsigned long long) cur << 16) | ((unsigned long long) chipletOf(dst) << 8) | (od << 4) | m, (float) b);
                note(by_m_dst, ((unsigned long long) cur << 20) | ((unsigned long long) dst << 4) | m, (float) b);
            } else {
                note(by_o_dst_dest, ((unsigned long long) cur << 16) | ((unsigned long long) dst << 4) | od, (float) b);
            }
        }
    };

    for (int cur = 0; cur < NROUTERS; cur++) {
        for (int dst = 0; dst < NCHIP_ROUTERS; dst++) {
            const int cd = chipletOf(dst);
            std::vector<DeftTopology::VerticalLinkInfo> de = DeftTopology::functionalVerticalLinksForChiplet(cd);
            if (isInterposer(cur)) {
                const int cs = (cd + 1) % C;
                const int src = DeftTopology::chipletRouterId(cs, 0, 0);
                for (int sub = 1; sub < (1 << de.size()); sub++) {
                    VlMask en = 0;
                    for (size_t i = 0; i < de.size(); i++)
                        if (sub >> i & 1)
                            en |= bit(de[i].vl_id);
                    for (int dir_in = 0; dir_in < 6; dir_in++)
                        if (dir_in != DIRECTION_LOCAL)
                            visit(cur, src, dst, dir_in, 0, en);
                }
            } else if (chipletOf(cur) == cd) {
                const int other = DeftTopology::chipletRouterId((cd + 1) % C, 0, 0);
                for (int dir_in = 0; dir_in < 6; dir_in++) {
                    visit(cur, cur, dst, dir_in, 0, 0);     // intra-chiplet
                    visit(cur, other, dst, dir_in, 0, 0);   // destination phase
                }
            } else {
                const VlMask entries = functionalMask(cd);
                std::vector<DeftTopology::VerticalLinkInfo> se = DeftTopology::functionalVerticalLinksForChiplet(chipletOf(cur));
                for (int sub = 1; sub < (1 << se.size()); sub++) {
                    VlMask ex = 0;
                    for (size_t i = 0; i < se.size(); i++)
                        if (sub >> i & 1)
                            ex |= bit(se[i].vl_id);
                    for (int dir_in = 0; dir_in < 6; dir_in++)
                        if (dir_in != DIRECTION_HUB)
                            visit(cur, cur, dst, dir_in, ex, entries);
                }
            }
        }
    }
    printf("%s scope %c mask %s: inputs %lu, moves compared %lu, MISMATCHES %lu\n", size.c_str(), scope, argv[3], inputs, moves, mismatches);
    report("(router, o, M)", by_o_m);
    report("(router, o, M, dest chiplet)", by_o_m_chip);
    report("(router, M, dst)", by_m_dst);
    report("(router, o, dst), dest phase", by_o_dst_dest);
    for (int l = 0; l < 2; l++) {
        printf("  offered outputs before the VN rules, %s:", l ? "interposer" : "chiplet");
        for (int k = 0; k < 7; k++)
            if (offered[l][k])
                printf(" %d: %lu", k, offered[l][k]);
        printf("\n");
    }
    return mismatches ? 3 : 0;
}
