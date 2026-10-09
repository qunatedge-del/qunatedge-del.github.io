#include <math.h>
#include "ktype.h"

/* ---- inverse: mV -> degC, NIST ITS-90 Table (type K) ---- */
static const double inv_neg[]  = {   /* -5.891 .. 0 mV      (-200 .. 0 C)   */
    0.0, 2.5173462e1, -1.1662878, -1.0833638, -8.9773540e-1,
    -3.7342377e-1, -8.6632643e-2, -1.0450598e-2, -5.1920577e-4 };
static const double inv_mid[]  = {   /* 0 .. 20.644 mV      (0 .. 500 C)    */
    0.0, 2.508355e1, 7.860106e-2, -2.503131e-1, 8.315270e-2,
    -1.228034e-2, 9.804036e-4, -4.413030e-5, 1.057734e-6, -1.052755e-8 };
static const double inv_high[] = {   /* 20.644 .. 54.886 mV (500 .. 1372 C) */
    -1.318058e2, 4.830222e1, -1.646031, 5.464731e-2, -9.650715e-4,
    8.802193e-6, -3.110810e-8 };

/* ---- forward: degC -> mV ---- */
static const double fwd_neg[] = {    /* -270 .. 0 C */
    0.0, 0.394501280250e-1, 0.236223735980e-4, -0.328589067840e-6,
    -0.499048287770e-8, -0.675090591730e-10, -0.574103274280e-12,
    -0.310888728940e-14, -0.104516093650e-16, -0.198892668780e-19,
    -0.163226974860e-22 };
static const double fwd_pos[] = {    /* 0 .. 1372 C */
    -0.176004136860e-1, 0.389212049750e-1, 0.185587700320e-4,
    -0.994575928740e-7, 0.318409457190e-9, -0.560728448890e-12,
    0.560750590590e-15, -0.320207200030e-18, 0.971511471520e-22,
    -0.121047212750e-25 };

static double poly(const double *c, int n, double x)
{
    double r = c[n - 1];
    for (int i = n - 2; i >= 0; i--) r = r * x + c[i];
    return r;
}

int ktype_mv_to_c(double mv, double *deg_c)
{
    int rc = 0;
    if (mv < KTYPE_MV_MIN) { mv = KTYPE_MV_MIN; rc = -1; }
    if (mv > KTYPE_MV_MAX) { mv = KTYPE_MV_MAX; rc = -1; }

    if (mv < 0.0)         *deg_c = poly(inv_neg,  9, mv);
    else if (mv < 20.644) *deg_c = poly(inv_mid, 10, mv);
    else                  *deg_c = poly(inv_high, 7, mv);
    return rc;
}

double ktype_c_to_mv(double t)
{
    if (t < 0.0)
        return poly(fwd_neg, 11, t);
    {
        const double a0 = 0.118597600000, a1 = -0.118343200000e-3,
                     a2 = 0.126968600000e3;
        double d = t - a2;
        return poly(fwd_pos, 10, t) + a0 * exp(a1 * d * d);
    }
}

int ktype_compensate(double mv_measured, double cjc_c, double *deg_c)
{
    return ktype_mv_to_c(mv_measured + ktype_c_to_mv(cjc_c), deg_c);
}
