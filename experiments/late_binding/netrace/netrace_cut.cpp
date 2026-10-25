// netrace_cut: extract the first part of a region of a Netrace trace into a plain packet list (v13, Part E).
//
// Uses the Netrace reader library (netrace.cpp/.h: Netrace 1.0 by J. Hestness, UT Austin, BSD-style license in
// NETRACE_LICENSE; adapted to compile as C++). Reads the trace header, seeks to region R and writes every packet
// whose cycle is below region_start + MAX_CYCLES (and at most MAX_PACKETS packets) as one line:
//   cycle id type src dst node_types num_deps dep_1 ... dep_n
// where the deps are the ids of the packets that depend on this packet (Netrace's downward dependencies).
// A header line '# benchmark nodes region region_start region_cycles region_packets max_cycles' comes first.
// Usage: netrace_cut TRACE.tra.bz2 REGION MAX_CYCLES MAX_PACKETS OUT.txt
// TRACE = '-' reads the bzip2 stream from standard input (e.g. piped from the download): the earlier regions are
// then skipped by reading their packets (no seek), and the program stops reading after the window, which also
// stops the download.
#include <cstdio>
#include <cstdlib>
#include <string>
#include <unistd.h>

#include "netrace.h"

int main(int argc, char **argv)
{
    if (argc != 6) {
        fprintf(stderr, "usage: %s TRACE REGION MAX_CYCLES MAX_PACKETS OUT\n", argv[0]);
        return 1;
    }
    const int region = atoi(argv[2]);
    const unsigned long long max_cycles = strtoull(argv[3], 0, 10);
    const unsigned long long max_packets = strtoull(argv[4], 0, 10);
    nt_open_trfile(argv[1]);
    nt_disable_dependencies();      // only the dependency lists are copied; tracking happens in the simulator
    nt_header_t *h = nt_get_trheader();
    if (region < 0 || region >= (int) h->num_regions) {
        fprintf(stderr, "region %d not in trace (%u regions)\n", region, h->num_regions);
        return 1;
    }
    unsigned long long start = 0;
    for (int i = 0; i < region; i++)
        start += h->regions[i].num_cycles;
    const bool streaming = std::string(argv[1]) == "-";
    if (streaming) {
        unsigned long long skip = 0;
        for (int i = 0; i < region; i++)
            skip += h->regions[i].num_packets;
        for (unsigned long long k = 0; k < skip; k++) {
            nt_packet_t *q = nt_read_packet();
            if (q == NULL) {
                fprintf(stderr, "trace ended while skipping to region %d\n", region);
                return 1;
            }
            nt_packet_free(q);
        }
    } else {
        nt_seek_region(&h->regions[region]);
    }
    FILE *out = fopen(argv[5], "w");
    fprintf(out, "# %s %u %d %llu %llu %llu %llu\n", h->benchmark_name, (unsigned) h->num_nodes, region, start,
            h->regions[region].num_cycles, h->regions[region].num_packets, max_cycles);
    unsigned long long n = 0;
    nt_packet_t *p;
    while (n < max_packets && (p = nt_read_packet()) != NULL) {
        if (p->cycle >= start + max_cycles)
            break;
        fprintf(out, "%llu %u %u %u %u %u %u", p->cycle, p->id, (unsigned) p->type, (unsigned) p->src,
                (unsigned) p->dst, (unsigned) p->node_types, (unsigned) p->num_deps);
        for (int i = 0; i < p->num_deps; i++)
            fprintf(out, " %u", p->deps[i]);
        fprintf(out, "\n");
        n++;
        nt_packet_free(p);
    }
    fclose(out);
    if (streaming) {
        fprintf(stderr, "%s: %llu packets written (streamed)\n", h->benchmark_name, n);
        _exit(0);                   // do not drain the rest of the stream
    }
    fprintf(stderr, "%s: %llu packets written (region %d starts at cycle %llu, %llu cycles, %llu packets)\n",
            h->benchmark_name, n, region, start, h->regions[region].num_cycles, h->regions[region].num_packets);
    nt_close_trfile();
    return 0;
}
