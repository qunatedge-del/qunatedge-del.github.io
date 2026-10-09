/* Host-side self test:  gcc -O2 -o test_ktype test_ktype.c ktype.c -lm && ./test_ktype */
#include <stdio.h>
#include <math.h>
#include "ktype.h"

/* NIST ITS-90 type K reference points (degC, mV). Inverse tolerance 0.07 C:
 * the published ITS-90 inverse polynomials are accurate to ~0.04 C, and the
 * worst case over -200..1372 C is 0.067 C at the -200 C end. */
static const double ref[][2] = {
    {-200,-5.891},{-100,-3.554},{-50,-1.889},{-10,-0.392},{0,0.000},{10,0.397},
    {25,1.000},{50,2.023},{100,4.096},{200,8.138},{300,12.209},{400,16.397},
    {500,20.644},{600,24.905},{800,33.275},{1000,41.276},{1200,48.838},{1372,54.886}};

int main(void)
{
    int fail = 0;
    for (unsigned i = 0; i < sizeof ref / sizeof ref[0]; i++) {
        double mv = ktype_c_to_mv(ref[i][0]), t;
        ktype_mv_to_c(ref[i][1], &t);
        double e_mv = fabs(mv - ref[i][1]);      /* forward error, mV  */
        double e_c  = fabs(t - ref[i][0]);       /* inverse error, degC */
        int bad = e_mv > 0.0015 || e_c > 0.07;
        printf("%7.1f C  fwd %8.4f mV (ref %7.3f, err %.4f)  inv %8.3f C (err %.3f) %s\n",
               ref[i][0], mv, ref[i][1], e_mv, t, e_c, bad ? "FAIL" : "ok");
        fail += bad;
    }
    /* compensation round trip: hot 300 C, cold junction 27.3 C */
    double mv = ktype_c_to_mv(300.0) - ktype_c_to_mv(27.3), t;
    ktype_compensate(mv, 27.3, &t);
    printf("round trip 300C/CJ27.3C -> %.3f C\n", t);
    fail += fabs(t - 300.0) > 0.07;
    printf(fail ? "TEST FAILED\n" : "ALL PASS\n");
    return fail != 0;
}
