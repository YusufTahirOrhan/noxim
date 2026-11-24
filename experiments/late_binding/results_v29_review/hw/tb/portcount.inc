// v29 Part E4: flits per input port of every router, for the activity of the power estimate.
// This file is appended to the instrumented COPY of src/DeftLateBinding.cpp by patch_ports.py (the repository's sources and
// bin/noxim are not touched). With the environment variable LB29_PORTS=<file> the instrumented simulator counts, in the
// measured window, every flit that an input buffer takes (per router, input port and VC), the heads among them, and the sum
// over the cycles of the fill of every input buffer; the file is written when the simulator exits.
// Nothing else changes: no random number is drawn and no simulator state is written. experiments_v29_hw2.py (e4_loads) checks
// that the statistics file of such a run is byte-identical to that of bin/noxim.
// One line per router: R id layer(0 chiplet, 1 interposer) has_vl cycles, then for port 0..5 (N, E, S, W, Local, vertical link)
// and VC 0, 1: flits heads fill_sum.
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

namespace DeftLB {

namespace {

struct PortCount {
    long flits[6][2], heads[6][2], fill[6][2], cycles;
    int layer, has_vl;
    bool seen;
    PortCount() : cycles(0), layer(0), has_vl(0), seen(false)
    {
        for (int p = 0; p < 6; p++)
            for (int v = 0; v < 2; v++)
                flits[p][v] = heads[p][v] = fill[p][v] = 0;
    }
};

std::vector<PortCount> g_pc;
std::string g_pc_file;
bool g_pc_init = false, g_pc_on = false;

struct PortDump {
    ~PortDump()
    {
        if (!g_pc_on)
            return;
        FILE *f = fopen(g_pc_file.c_str(), "w");
        if (!f)
            return;
        for (size_t r = 0; r < g_pc.size(); r++) {
            const PortCount &c = g_pc[r];
            if (!c.seen)
                continue;
            fprintf(f, "R %d %d %d %ld", (int) r, c.layer, c.has_vl, c.cycles);
            for (int p = 0; p < 6; p++)
                for (int v = 0; v < 2; v++)
                    fprintf(f, " %ld %ld %ld", c.flits[p][v], c.heads[p][v], c.fill[p][v]);
            fprintf(f, "\n");
        }
        fclose(f);
    }
} g_pc_dump;

PortCount *pcOf(int router, int port, int vc)
{
    if (router < 0 || port < 0 || port > 5 || vc < 0 || vc > 1)
        return 0;
    const double now = sc_time_stamp().to_double() / GlobalParams::clock_period_ps;
    if (now - GlobalParams::reset_time < GlobalParams::stats_warm_up_time)
        return 0;
    if (router >= (int) g_pc.size())
        g_pc.resize(router + 1);
    PortCount &c = g_pc[router];
    if (!c.seen) {
        c.seen = true;
        c.layer = isInterposer(router) ? 1 : 0;
        c.has_vl = vlAtRouter(router) >= 0 ? 1 : 0;
    }
    return &c;
}

} // namespace

bool portsOn()
{
    if (!g_pc_init) {
        g_pc_init = true;
        const char *p = getenv("LB29_PORTS");
        if (p) {
            g_pc_file = p;
            g_pc_on = true;
        }
    }
    return g_pc_on;
}

// a flit was stored in the input buffer of (port, vc)
void portFlit(int router, int port, int vc, bool head)
{
    PortCount *c = pcOf(router, port, vc);
    if (!c)
        return;
    c->flits[port][vc]++;
    if (head)
        c->heads[port][vc]++;
}

// once per router, port, VC and cycle: the fill of the input buffer after this cycle's arrival
void portFill(int router, int port, int vc, int fill)
{
    PortCount *c = pcOf(router, port, vc);
    if (!c)
        return;
    c->fill[port][vc] += fill;
    if (port == 0 && vc == 0)
        c->cycles++;
}

} // namespace DeftLB
