// v25 F2: Verilator checker of the decision unit (hw/rtl/lb25_units.v, wrapper vl25.v) against selection vectors dumped
// from simulator runs (vecdump.inc). The same checks as tb_sel25 of tb25.v.
// Usage: Vvl_sel25 VECFILE ORDER_O DBIAS CUT_A CUT_M CUT_B      (the five values must be those the model was built with)
// Per vector: offered outputs, pruned mask of every offered output, cost of every offered output (when the simulator
// evaluated the selection), and the choice. The simulator breaks ties at random; the vector's choice is given to the unit
// as the start of its rotating priority, so the unit returns it if and only if it is an output of least cost. Then the
// pointer is swept over its five positions: the unit must return the first output of least cost at or after the pointer,
// wrapping, where the outputs of least cost are taken from the simulator's costs (or the only offered output).
#include "Vvl_sel25.h"
#include "verilated.h"
#include <cstdio>
#include <cstdlib>

int main(int argc, char **argv)
{
    if (argc < 7) { fprintf(stderr, "usage: %s VECFILE ORDER_O DBIAS CUT_A CUT_M CUT_B\n", argv[0]); return 2; }
    FILE *f = fopen(argv[1], "r");
    if (!f) { fprintf(stderr, "cannot open %s\n", argv[1]); return 2; }
    const int order_o = atoi(argv[2]), dbias = atoi(argv[3]), cut_a = atoi(argv[4]), cut_m = atoi(argv[5]), cut_b = atoi(argv[6]);
    const int ncut = cut_a + cut_m + cut_b;
    Vvl_sel25 *t = new Vvl_sel25;
    long n = 0, bad = 0, multi = 0, nodef = 0, sweeps = 0, ml[5] = {0, 0, 0, 0, 0};
    unsigned v[53];
    for (;;) {
        int r = 0;
        for (int i = 0; i < 53; i++)
            r += fscanf(f, "%x", &v[i]);
        if (r != 53)
            break;
        const unsigned kind = v[0], x = v[1], y = v[2], last = v[3], vn = v[4], dx = v[5], dy = v[6], mask = v[7], hub = v[8], def = v[9];
        const unsigned *fo = &v[10], *g = &v[15];
        const unsigned off = v[40], *pr = &v[41], hascost = v[46], *c = &v[47], choice = v[52];
        (void) kind;
        // the other VC carries the complement, so that a read of the wrong VC shows
        unsigned occ_self = 0, nb[5] = {0, 0, 0, 0, 0};
        for (int o = 0; o < 5; o++) {
            const unsigned a = fo[o] & 7, na = ~fo[o] & 7;
            occ_self |= (vn ? na : a) << ((o * 2 + 0) * 3);
            occ_self |= (vn ? a : na) << ((o * 2 + 1) * 3);
            for (int z = 0; z < 5; z++) {
                const unsigned b = g[o * 5 + z] & 7, nbv = ~g[o * 5 + z] & 7;
                const bool vc1 = (o == 4) || vn;
                nb[o] |= (vc1 ? nbv : b) << (z * 6);
                nb[o] |= (vc1 ? b : nbv) << (z * 6 + 3);
            }
        }
        t->x = x; t->y = y; t->dx = dx; t->dy = dy; t->mask = mask; t->last = last; t->vn = vn; t->def = def & 3; t->rnd = choice;
        t->occ_self = occ_self; t->nb0 = nb[0]; t->nb1 = nb[1]; t->nb2 = nb[2]; t->nb3 = nb[3]; t->nb4 = nb[4];
        t->sel = 0;
        t->clk = 0;
        t->eval();
        for (int i = 0; i < ncut; i++) {
            t->clk = 1; t->eval();
            t->clk = 0; t->eval();
        }
        n++;
        int cnt = 0;
        for (int o = 0; o < 5; o++)
            cnt += (off >> o) & 1;
        if (cnt > 1) { multi++; ml[last]++; }
        if (dbias != 0 && def == 7) nodef++;
        const unsigned units[4] = {0, 1 + last, 6, 7 + last};
        bool ok = true;
        for (int uu = 0; uu < (hub ? 2 : 4); uu++) {
            t->sel = units[uu];
            t->eval();
            if (t->off != off) ok = false;
            for (int o = 0; o < 5; o++)
                if ((off >> o) & 1) {
                    if (((t->pr >> (4 * o)) & 15) != pr[o]) ok = false;
                    if (hascost && ((t->cmin >> (8 * o)) & 255) != c[o]) ok = false;
                }
            if (t->dec != choice) ok = false;
            // pointer sweep (the tie break reads the pointer in the last stage, so no clock is needed)
            unsigned tieset = 0, cmin = 0xffffffffu;
            if (hascost) {
                for (int o = 0; o < 5; o++)
                    if (((off >> o) & 1) && c[o] < cmin) cmin = c[o];
                for (int o = 0; o < 5; o++)
                    if (((off >> o) & 1) && c[o] == cmin) tieset |= 1u << o;
            } else if (cnt == 1) {
                tieset = off;
            }
            if (tieset)
                for (unsigned r = 0; r < 5; r++) {
                    unsigned expd = 7;
                    for (unsigned k = 0; k < 5 && expd == 7; k++)
                        if ((tieset >> ((r + k) % 5)) & 1) expd = (r + k) % 5;
                    t->rnd = r;
                    t->eval();
                    if (t->dec != expd) ok = false;
                    sweeps++;
                }
            t->rnd = choice;
            t->eval();
        }
        if (!ok) {
            bad++;
            if (bad < 10) {
                t->sel = 0;
                t->eval();
                printf("MISMATCH kind %u pos %u,%u last %u vn %u dst %u,%u mask %x hub %u def %u: offered %x exp %x dec %u exp %u cmin %llx exp %u %u %u %u %u\n",
                       kind, x, y, last, vn, dx, dy, mask, hub, def, (unsigned) t->off, off, (unsigned) t->dec, choice, (unsigned long long) t->cmin, c[0], c[1], c[2], c[3], c[4]);
            }
        }
    }
    printf("RESULT sel order_o=%d dbias=%d cuts=%d%d%d vectors=%ld mismatches=%ld multi=%ld multi_by_last=%ld,%ld,%ld,%ld,%ld no_default=%ld pointer_checks=%ld\n",
           order_o, dbias, cut_a, cut_m, cut_b, n, bad, multi, ml[0], ml[1], ml[2], ml[3], ml[4], nodef, sweeps);
    t->final();
    delete t;
    return 0;
}
