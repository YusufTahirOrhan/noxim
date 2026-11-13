// v26 A3: every hop of a head flit, for the replay through the formal model (experiments_v26_conf.py).
// This file is appended to a COPY of src/DeftLateBinding.cpp by patch_hopdump.py (the repository's sources and bin/noxim
// are not touched). With the environment variable LB26_HOP=<prefix> the instrumented simulator writes
//   <prefix>.topo.txt  once: the geometry and the options the replay needs (key value pairs, one per line)
//   <prefix>.hop.bin   one fixed-size binary record per head flit forwarded by a router (HopRec below)
// Nothing else changes: no random number is drawn and no simulator state is written. The offered outputs are computed again
// at the forward with the run's own routing function and VN rule (both read-only); experiments_v26_conf.py checks that the
// statistics file of every instrumented run is byte-identical to that of bin/noxim.
#include <cstdio>
#include <cstdlib>
#include <stdint.h>

namespace DeftLB {

namespace {

FILE *g_hop = 0;
bool g_hop_init = false;
Flit g_hop_before;                   // the head as it stands in the input buffer, before onHeadForward prunes its masks

struct HopRec {
    int32_t router;                  // router id (chiplet routers first, then the interposer routers)
    int32_t dir_in;                  // input port: 0 N, 1 E, 2 S, 3 W, 4 Local (injected), 5 Hub (arrived over a VL)
    int32_t vc_in;                   // VC of the head in the input buffer: its VN before the hop
    int32_t src, dst;
    int32_t offered;                 // bit d = output d is offered by the routing function and allowed by the VN rule
    int32_t out_dir;                 // output taken (4 = Local: the head leaves the network)
    int32_t out_vc;                  // VC on the output: the VN after the hop
    int32_t lut_exit, lut_entry;     // plain DEFT, inter-chiplet: the VL ids the LUT selects; -1 otherwise
    uint64_t exit_before, entry_before, exit_after, entry_after;   // DEFT_LB candidate masks (bit = VL id)
};

void hopInit()
{
    if (g_hop_init)
        return;
    g_hop_init = true;
    const char *p = getenv("LB26_HOP");
    if (!p)
        return;
    const std::string s(p);
    FILE *t = fopen((s + ".topo.txt").c_str(), "w");
    if (!t)
        return;
    fprintf(t, "record_bytes %d\n", (int) sizeof(HopRec));
    fprintf(t, "W %d\nH %d\nNCHIP_ROUTERS %d\nNROUTERS %d\nNVL %d\n", W, H, NCHIP_ROUTERS, NROUTERS, NVL);
    fprintf(t, "chiplet_w %d\nchiplet_h %d\ngrid_w %d\n", DeftTopology::ChipletLocalWidth, DeftTopology::ChipletLocalHeight, DeftTopology::ChipletGridWidth);
    fprintf(t, "DIRECTION_LOCAL %d\nDIRECTION_HUB %d\n", DIRECTION_LOCAL, DIRECTION_HUB);
    for (int d = 0; d < 4; d++)
        fprintf(t, "dir %d %d %d\n", d, DX[d], DY[d]);
    for (int v = 0; v < NVL; v++) {
        const DeftTopology::VerticalLinkInfo *l = DeftTopology::verticalLinkById(v);
        fprintf(t, "vl %d %d %d %d %d %d\n", v, l ? (int) l->is_functional : -1, DeftTopology::chipletEndpointForVerticalLink(v),
                DeftTopology::interposerEndpointForVerticalLink(v), l ? (int) l->slot : -1, chipletOf(DeftTopology::chipletEndpointForVerticalLink(v)));
    }
    fprintf(t, "routing %s\n", GlobalParams::routing_algorithm.c_str());
    fprintf(t, "lb_active %d\nchip_tm %d\nipos_tm %d\nexit_policy %s\nentry_policy %s\n", isActive() ? 1 : 0, g_config.chip_tm, g_config.ipos_tm,
            policyName(g_config.exit_policy).c_str(), policyName(g_config.entry_policy).c_str());
    fprintf(t, "vn_rules %d\nvn_rr %d\nup_keep %d\nrr_fallback %d\n", DeftVirtualNetwork::rulesActive() ? 1 : 0, DeftVirtualNetwork::roundRobinActive() ? 1 : 0,
            DeftVirtualNetwork::upKeep() ? 1 : 0, DeftVirtualNetwork::rrFallback() ? 1 : 0);
    fprintf(t, "lut_entry %s\nn_vc %d\n", GlobalParams::deft_lut_entry.c_str(), GlobalParams::n_virtual_channels);
    fclose(t);
    g_hop = fopen((s + ".hop.bin").c_str(), "wb");
}

} // namespace

bool hopOn()
{
    hopInit();
    return g_hop != 0;
}

void hopBefore(const Flit &flit)
{
    if (hopOn())
        g_hop_before = flit;
}

// Called for a head flit at the forward, after onHeadForward: `after` carries the masks the next router will see, and its
// vc_id is still the input VC.
void hopAfter(Router *router, int dir_in, int out_dir, int out_vc, const Flit &after)
{
    if (!hopOn())
        return;
    const Flit &b = g_hop_before;
    HopRec r;
    r.router = router->local_id;
    r.dir_in = dir_in;
    r.vc_in = b.vc_id;
    r.src = b.src_id;
    r.dst = b.dst_id;
    r.out_dir = out_dir;
    r.out_vc = out_vc;
    r.exit_before = b.deft_exit_mask;
    r.entry_before = b.deft_entry_mask;
    r.exit_after = after.deft_exit_mask;
    r.entry_after = after.deft_entry_mask;
    r.lut_exit = r.lut_entry = -1;
    RouteData rd;
    rd.current_id = router->local_id;
    rd.src_id = b.src_id;
    rd.dst_id = b.dst_id;
    rd.dir_in = dir_in;
    rd.vc_id = b.vc_id;
    rd.deft_exit_mask = b.deft_exit_mask;
    rd.deft_entry_mask = b.deft_entry_mask;
    r.offered = 0;
    if (rd.dst_id == rd.current_id) {
        r.offered = 1 << DIRECTION_LOCAL;            // Router::route: the destination router offers the Local port only
    } else {
        const std::vector<int> all = router->routingAlgorithm->route(router, rd);
        for (size_t k = 0; k < all.size(); k++)
            if (all[k] >= 0 && all[k] < 31 && DeftVirtualNetwork::isOutputDirectionAllowed(rd, all[k]))
                r.offered |= 1 << all[k];
    }
    if (!isActive() && chipletOf(rd.src_id) >= 0 && chipletOf(rd.dst_id) >= 0 && chipletOf(rd.src_id) != chipletOf(rd.dst_id)) {
        DeftVerticalLinkLut::Entry e;
        if (DeftVerticalLinkLut::lookupPair(chipletOf(rd.src_id), rd.src_id, chipletOf(rd.dst_id), rd.dst_id, &e, 0)) {
            r.lut_exit = e.source_exit.selected_vl_id;
            r.lut_entry = e.destination_entry.selected_vl_id;
        }
    }
    fwrite(&r, sizeof(r), 1, g_hop);
}

} // namespace DeftLB
