/*
 * Netrace-driven traffic (v13 Part E). See NetraceDriver.h.
 */

#include "NetraceDriver.h"

#include <cstdlib>
#include <deque>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

#include "GlobalParams.h"

namespace NetraceDriver {

namespace {

const int L2_LATENCY = 8;      // Netrace example simulator: injection delay after a dependency clears

struct Pkt {
    unsigned long long cycle;
    unsigned int id;
    int type, src, dst, size;
    std::vector<unsigned int> deps;    // ids of the packets that depend on this one
};

bool g_loaded = false;
std::vector<Pkt> g_pkts;
std::unordered_map<unsigned int, int> g_ref;     // id -> number of undelivered in-window packets it depends on
size_t g_next = 0;                               // next packet to read
std::vector<std::deque<std::pair<int, unsigned long long> > > g_inject;   // per node: (packet, ready trace cycle)
std::vector<std::vector<int> > g_waiting;        // per node: packets waiting for dependencies
unsigned long long g_region_start = 0;
double g_last_tick = -1.0;
unsigned long long g_tcycle = 0;
unsigned long g_injected = 0, g_delivered = 0, g_self = 0, g_waited = 0;
double g_last_delivery = 0.0;
std::string g_benchmark;

int sizeFlits(int type)
{
    // Netrace packet sizes in bytes (netrace.c nt_packet_sizes): control 8, data 72
    static const int bytes[] = { -1, 8, 72, 72, 72, 8, 72, -1, -1, -1, -1, -1, -1, 8, 8, 8, 72, -1, -1, -1, -1, -1,
                                 -1, -1, -1, 8, -1, 8, 8, 8, 72 };
    int b = (type >= 0 && type < 31 && bytes[type] > 0) ? bytes[type] : 8;
    const int flit_bytes = GlobalParams::flit_size / 8;
    int f = (b + flit_bytes - 1) / flit_bytes;
    return f < 2 ? 2 : f;
}

void deliver(int idx)
{
    const Pkt &p = g_pkts[idx];
    for (size_t i = 0; i < p.deps.size(); i++) {
        std::unordered_map<unsigned int, int>::iterator it = g_ref.find(p.deps[i]);
        if (it != g_ref.end() && it->second > 0)
            it->second--;
    }
}

bool cleared(int idx)
{
    if (!GlobalParams::netrace_deps)
        return true;
    std::unordered_map<unsigned int, int>::const_iterator it = g_ref.find(g_pkts[idx].id);
    return it == g_ref.end() || it->second == 0;
}

void load()
{
    g_loaded = true;
    std::ifstream in(GlobalParams::netrace_file.c_str());
    if (!in) {
        std::cerr << "netrace: cannot open " << GlobalParams::netrace_file << std::endl;
        exit(1);
    }
    std::string line;
    unsigned long long max_cycles = 0;
    while (std::getline(in, line)) {
        if (line.empty())
            continue;
        std::istringstream ss(line);
        if (line[0] == '#') {
            std::string hash;
            unsigned nodes, region;
            unsigned long long rcycles, rpackets;
            ss >> hash >> g_benchmark >> nodes >> region >> g_region_start >> rcycles >> rpackets >> max_cycles;
            continue;
        }
        Pkt p;
        unsigned nd, nodetypes;
        ss >> p.cycle >> p.id >> p.type >> p.src >> p.dst >> nodetypes >> nd;
        if (p.cycle >= g_region_start + (unsigned long long) GlobalParams::netrace_window)
            break;
        p.deps.resize(nd);
        for (unsigned i = 0; i < nd; i++)
            ss >> p.deps[i];
        p.size = sizeFlits(p.type);
        g_pkts.push_back(p);
    }
    for (size_t k = 0; k < g_pkts.size(); k++)
        for (size_t i = 0; i < g_pkts[k].deps.size(); i++)
            g_ref[g_pkts[k].deps[i]]++;
    const int nodes = 4096;     // indexed by router id (trace nodes are chiplet routers 0..63)
    g_inject.assign(nodes, std::deque<std::pair<int, unsigned long long> >());
    g_waiting.assign(nodes, std::vector<int>());
}

void tick(double now)
{
    if (!g_loaded)
        load();
    g_tcycle = g_region_start + (unsigned long long) (now - GlobalParams::reset_time);
    while (g_next < g_pkts.size() && g_pkts[g_next].cycle <= g_tcycle) {
        const int idx = (int) g_next++;
        const Pkt &p = g_pkts[idx];
        if (p.src == p.dst) {             // not a network packet: delivered at once
            g_self++;
            deliver(idx);
            continue;
        }
        if (cleared(idx))
            g_inject[p.src].push_back(std::make_pair(idx, p.cycle));
        else {
            g_waiting[p.src].push_back(idx);
            g_waited++;
        }
    }
    for (size_t n = 0; n < g_waiting.size(); n++) {
        std::vector<int> &w = g_waiting[n];
        for (size_t i = 0; i < w.size();) {
            if (cleared(w[i])) {
                g_inject[n].push_back(std::make_pair(w[i], g_tcycle + L2_LATENCY));
                w.erase(w.begin() + i);
            } else {
                i++;
            }
        }
    }
}

} // namespace

bool active()
{
    return !GlobalParams::netrace_file.empty();
}

bool popReady(int node, double now, int *dst, int *size, int *trace_id)
{
    if (now != g_last_tick) {
        g_last_tick = now;
        tick(now);
    }
    if (node < 0 || node >= (int) g_inject.size() || g_inject[node].empty())
        return false;
    // the queue is ordered by arrival; release the front once its ready cycle has come
    std::pair<int, unsigned long long> f = g_inject[node].front();
    if (f.second > g_tcycle)
        return false;
    g_inject[node].pop_front();
    const Pkt &p = g_pkts[f.first];
    *dst = p.dst;
    *size = p.size;
    *trace_id = f.first;
    g_injected++;
    return true;
}

void onDelivered(int trace_id, double now)
{
    if (trace_id < 0 || trace_id >= (int) g_pkts.size())
        return;
    deliver(trace_id);
    g_delivered++;
    g_last_delivery = now;
}

bool finished()
{
    if (!g_loaded || g_next < g_pkts.size())
        return false;
    for (size_t n = 0; n < g_inject.size(); n++)
        if (!g_inject[n].empty() || !g_waiting[n].empty())
            return false;
    return g_delivered == g_injected;
}

long completionCycle()
{
    return (long) (g_last_delivery - GlobalParams::reset_time);
}

void writeJsonFields(std::ostream &out)
{
    out << "    \"netrace_benchmark\": \"" << g_benchmark << "\", \"netrace_window_cycles\": "
        << GlobalParams::netrace_window << ", \"netrace_dependencies\": " << GlobalParams::netrace_deps << ","
        << std::endl;
    out << "    \"netrace_packets\": " << g_pkts.size() << ", \"netrace_injected\": " << g_injected
        << ", \"netrace_delivered\": " << g_delivered << ", \"netrace_self_packets\": " << g_self
        << ", \"netrace_waited_for_dependencies\": " << g_waited << "," << std::endl;
    out << "    \"netrace_finished\": " << (finished() ? "true" : "false") << ", \"netrace_completion_cycle\": "
        << completionCycle() << "," << std::endl;
}

} // namespace NetraceDriver
