// v25 F2: Verilator checker of the logic at the buffer front (relation, the only output, the lookahead fallback; wrapper
// vl25.v) against the front vectors dumped from simulator runs (vecdump.inc). The same checks as tb_front25 of tb25.v.
// Usage: Vvl_front25 VECFILE ORDER_O
#include "Vvl_front25.h"
#include "verilated.h"
#include <cstdio>
#include <cstdlib>

int main(int argc, char **argv)
{
    if (argc < 3) { fprintf(stderr, "usage: %s VECFILE ORDER_O\n", argv[0]); return 2; }
    FILE *f = fopen(argv[1], "r");
    if (!f) { fprintf(stderr, "cannot open %s\n", argv[1]); return 2; }
    const int order_o = atoi(argv[2]);
    Vvl_front25 *t = new Vvl_front25;
    long n = 0, bad = 0, n_single = 0, n_fb = 0, n_fb_other = 0, n_held = 0, n_sel = 0;
    unsigned v[19];
    for (;;) {
        int r = 0;
        for (int i = 0; i < 19; i++)
            r += fscanf(f, "%x", &v[i]);
        if (r != 19)
            break;
        const unsigned x = v[0], y = v[1], last = v[2], vn = v[3], dx = v[4], dy = v[5], mask = v[6], hub = v[7], stored = v[8], held = v[9];
        const unsigned off = v[10], *pr = &v[11], fr = v[16], fbon = v[17], result = v[18];
        t->x = x; t->y = y; t->dx = dx; t->dy = dy; t->mask = mask; t->last = last; t->vn = vn; t->stored = stored; t->free = fr;
        n++;
        const unsigned units[4] = {0, 1 + last * 2 + vn, 11, 12 + last * 2 + vn};
        bool ok = true, single = false;
        for (int uu = 0; uu < (hub ? 2 : 4); uu++) {
            t->sel = units[uu];
            t->eval();
            single = t->single;
            if (t->off != off) ok = false;
            for (int o = 0; o < 5; o++)
                if (((off >> o) & 1) && ((t->pr >> (4 * o)) & 15) != pr[o]) ok = false;
            if (held != 7) {
                // the head already holds an output: no request is made (with the fallback the simulator returns that output)
                if (fbon && !t->single && result != held) ok = false;
            } else if (t->single) {
                if (t->only != result) ok = false;
            } else if (fbon && stored != 7) {
                if (t->fb != result) ok = false;
            }
        }
        if (held != 7) n_held++;
        else if (single) n_single++;
        else if (fbon && stored != 7) { n_fb++; if (result != stored) n_fb_other++; }
        else n_sel++;
        if (!ok) {
            bad++;
            if (bad < 10) {
                t->sel = 0;
                t->eval();
                printf("MISMATCH front pos %u,%u last %u vn %u dst %u,%u mask %x hub %u stored %u held %u: offered %x exp %x free %x result %u (fallback %u, only %u)\n",
                       x, y, last, vn, dx, dy, mask, hub, stored, held, (unsigned) t->off, off, fr, result, (unsigned) t->fb, (unsigned) t->only);
            }
        }
    }
    printf("RESULT front order_o=%d vectors=%ld mismatches=%ld one_output=%ld fallback_checked=%ld fallback_took_other=%ld head_holds_output=%ld decided_by_selection=%ld\n",
           order_o, n, bad, n_single, n_fb, n_fb_other, n_held, n_sel);
    t->final();
    delete t;
    return 0;
}
