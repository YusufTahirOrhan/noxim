/*
 * Netrace-driven traffic (v13 Part E; v15 Part G: second trace and compression). See NetraceDriver.h.
 */

#include "NetraceDriver.h"

#include <cmath>
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
const int TRACE_STRIDE = 1 << 26;   // trace_id = packet index + trace * TRACE_STRIDE

struct Pkt {
    unsigned long long cycle;
    unsigned int id;
    int type, src, dst, size;
    std::vector<unsigned int> deps;    // ids of the packets that depend on this one
};

// One trace reader with its own dependency tracking. All cycles are trace cycles; with the compression factor s,
// trace cycle = region start + s x (simulation cycle).
struct Trace {
    std::string file;
    bool loaded;
    std::vector<Pkt> pkts;
    std::unordered_map<unsigned int, int> ref;     // id -> number of undelivered in-window packets it depends on
    size_t next;                                   // next packet to read
    std::vector<std::deque<std::pair<int, unsigned long long> > > inject;   // per node: (packet, ready trace cycle)
    std::vector<std::vector<int> > waiting;        // per node: packets waiting for dependencies
    unsigned long long region_start;
    double last_tick;
    unsigned long long tcycle;
    unsigned long injected, delivered, self, waited;
    double last_delivery, latency_sum;
    std::string benchmark;
    Trace() : loaded(false), next(0), region_start(0), last_tick(-1.0), tcycle(0), injected(0), delivered(0), self(0),
              waited(0), last_delivery(0.0), latency_sum(0.0) {}
};

std::vector<Trace> g_traces;

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

void ensureTraces()
{
    if (!g_traces.empty())
        return;
    g_traces.push_back(Trace());
    g_traces.back().file = GlobalParams::netrace_file;
    if (!GlobalParams::netrace_file2.empty()) {
        g_traces.push_back(Trace());
        g_traces.back().file = GlobalParams::netrace_file2;
    }
}

void deliver(Trace &T, int idx)
{
    const Pkt &p = T.pkts[idx];
    for (size_t i = 0; i < p.deps.size(); i++) {
        std::unordered_map<unsigned int, int>::iterator it = T.ref.find(p.deps[i]);
        if (it != T.ref.end() && it->second > 0)
            it->second--;
    }
}

bool cleared(const Trace &T, int idx)
{
    if (!GlobalParams::netrace_deps)
        return true;
    std::unordered_map<unsigned int, int>::const_iterator it = T.ref.find(T.pkts[idx].id);
    return it == T.ref.end() || it->second == 0;
}

void load(Trace &T)
{
    T.loaded = true;
    std::ifstream in(T.file.c_str());
    if (!in) {
        std::cerr << "netrace: cannot open " << T.file << std::endl;
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
            ss >> hash >> T.benchmark >> nodes >> region >> T.region_start >> rcycles >> rpackets >> max_cycles;
            continue;
        }
        Pkt p;
        unsigned nd, nodetypes;
        ss >> p.cycle >> p.id >> p.type >> p.src >> p.dst >> nodetypes >> nd;
        if (p.cycle >= T.region_start + (unsigned long long) GlobalParams::netrace_window)
            break;
        p.deps.resize(nd);
        for (unsigned i = 0; i < nd; i++)
            ss >> p.deps[i];
        p.size = sizeFlits(p.type);
        T.pkts.push_back(p);
    }
    for (size_t k = 0; k < T.pkts.size(); k++)
        for (size_t i = 0; i < T.pkts[k].deps.size(); i++)
            T.ref[T.pkts[k].deps[i]]++;
    const int nodes = 4096;     // indexed by router id (trace nodes are chiplet routers 0..63)
    T.inject.assign(nodes, std::deque<std::pair<int, unsigned long long> >());
    T.waiting.assign(nodes, std::vector<int>());
}

void tick(Trace &T, double now)
{
    if (!T.loaded)
        load(T);
    const unsigned long long s = (unsigned long long) GlobalParams::netrace_compress;
    T.tcycle = T.region_start + s * (unsigned long long) (now - GlobalParams::reset_time);
    while (T.next < T.pkts.size() && T.pkts[T.next].cycle <= T.tcycle) {
        const int idx = (int) T.next++;
        const Pkt &p = T.pkts[idx];
        if (p.src == p.dst) {             // not a network packet: delivered at once
            T.self++;
            deliver(T, idx);
            continue;
        }
        if (cleared(T, idx))
            T.inject[p.src].push_back(std::make_pair(idx, p.cycle));
        else {
            T.waiting[p.src].push_back(idx);
            T.waited++;
        }
    }
    for (size_t n = 0; n < T.waiting.size(); n++) {
        std::vector<int> &w = T.waiting[n];
        for (size_t i = 0; i < w.size();) {
            if (cleared(T, w[i])) {
                // L2_LATENCY simulation cycles after the dependency cleared (s trace cycles per simulation cycle)
                T.inject[n].push_back(std::make_pair(w[i], T.tcycle + s * L2_LATENCY));
                w.erase(w.begin() + i);
            } else {
                i++;
            }
        }
    }
}

bool finishedTrace(const Trace &T)
{
    if (!T.loaded || T.next < T.pkts.size())
        return false;
    for (size_t n = 0; n < T.inject.size(); n++)
        if (!T.inject[n].empty() || !T.waiting[n].empty())
            return false;
    return T.delivered == T.injected;
}

} // namespace

bool active()
{
    return !GlobalParams::netrace_file.empty();
}

int traceCount()
{
    ensureTraces();
    return (int) g_traces.size();
}

bool popReady(int trace, int node, double now, int *dst, int *size, int *trace_id)
{
    ensureTraces();
    Trace &T = g_traces[trace];
    if (now != T.last_tick) {
        T.last_tick = now;
        tick(T, now);
    }
    if (node < 0 || node >= (int) T.inject.size() || T.inject[node].empty())
        return false;
    // the queue is ordered by arrival; release the front once its ready cycle has come
    std::pair<int, unsigned long long> f = T.inject[node].front();
    if (f.second > T.tcycle)
        return false;
    T.inject[node].pop_front();
    const Pkt &p = T.pkts[f.first];
    *dst = p.dst;
    *size = p.size;
    *trace_id = f.first + trace * TRACE_STRIDE;
    T.injected++;
    return true;
}

void onDelivered(int trace_id, double now, double timestamp)
{
    if (trace_id < 0)
        return;
    ensureTraces();
    const int t = trace_id / TRACE_STRIDE, idx = trace_id % TRACE_STRIDE;
    if (t >= (int) g_traces.size() || idx >= (int) g_traces[t].pkts.size())
        return;
    Trace &T = g_traces[t];
    deliver(T, idx);
    T.delivered++;
    T.last_delivery = now;
    T.latency_sum += now - timestamp;
}

bool finished()
{
    ensureTraces();
    for (size_t t = 0; t < g_traces.size(); t++)
        if (!finishedTrace(g_traces[t]))
            return false;
    return true;
}

long completionCycle()
{
    ensureTraces();
    double last = 0.0;
    for (size_t t = 0; t < g_traces.size(); t++)
        if (g_traces[t].last_delivery > last)
            last = g_traces[t].last_delivery;
    return (long) (last - GlobalParams::reset_time);
}

void writeJsonFields(std::ostream &out)
{
    ensureTraces();
    const Trace &A = g_traces[0];
    out << "    \"netrace_benchmark\": \"" << A.benchmark << "\", \"netrace_window_cycles\": "
        << GlobalParams::netrace_window << ", \"netrace_dependencies\": " << GlobalParams::netrace_deps << ","
        << std::endl;
    out << "    \"netrace_packets\": " << A.pkts.size() << ", \"netrace_injected\": " << A.injected
        << ", \"netrace_delivered\": " << A.delivered << ", \"netrace_self_packets\": " << A.self
        << ", \"netrace_waited_for_dependencies\": " << A.waited << "," << std::endl;
    out << "    \"netrace_finished\": " << (finished() ? "true" : "false") << ", \"netrace_completion_cycle\": "
        << completionCycle() << "," << std::endl;
    // fields only present with a second trace or compression (v15)
    if (GlobalParams::netrace_compress != 1)
        out << "    \"netrace_compress\": " << GlobalParams::netrace_compress << "," << std::endl;
    if (g_traces.size() > 1) {
        const Trace &B = g_traces[1];
        out << "    \"netrace2_benchmark\": \"" << B.benchmark << "\", \"netrace2_packets\": " << B.pkts.size()
            << ", \"netrace2_injected\": " << B.injected << ", \"netrace2_delivered\": " << B.delivered
            << ", \"netrace2_self_packets\": " << B.self << ", \"netrace2_waited_for_dependencies\": " << B.waited << ","
            << std::endl;
        for (size_t t = 0; t < g_traces.size(); t++) {
            const Trace &T = g_traces[t];
            out << "    \"netrace" << (t ? "2" : "1") << "_completion_cycle\": "
                << (long) (T.last_delivery - GlobalParams::reset_time) << ", \"netrace" << (t ? "2" : "1")
                << "_latency_mean\": " << (T.delivered ? T.latency_sum / T.delivered : 0.0) << "," << std::endl;
        }
    }
}

} // namespace NetraceDriver
