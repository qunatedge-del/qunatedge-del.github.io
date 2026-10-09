/*
 * ktype.h - NIST ITS-90 type-K thermocouple conversion (mV <-> degC)
 *
 *  ktype_mv_to_c()  : EMF (mV, referenced to 0 degC) -> temperature (degC)
 *                     valid  -5.891 .. 54.886 mV  (-200 .. 1372 degC)
 *  ktype_c_to_mv()  : temperature (degC) -> EMF (mV), used for cold-junction
 *                     compensation (valid -270 .. 1372 degC)
 *
 * Plain C99, no dependencies except <math.h> (exp) for the forward function.
 * On the SD93F115B (no FPU) 'double' is software-emulated; one conversion
 * costs well under 1 ms at 24 MHz, which is irrelevant at 1-10 Hz sampling.
 */
#ifndef KTYPE_H
#define KTYPE_H

#define KTYPE_MV_MIN   (-5.891)
#define KTYPE_MV_MAX   (54.886)

/* Returns 0 on success, -1 if mv is outside the valid range (result clamped). */
int    ktype_mv_to_c(double mv, double *deg_c);
double ktype_c_to_mv(double deg_c);

/*
 * Full compensation: mv_measured is the voltage across the thermocouple
 * (hot - cold junction); cjc_c is the cold-junction (terminal block) temp.
 * T_hot = inverse( mv_measured + forward(cjc_c) )
 */
int    ktype_compensate(double mv_measured, double cjc_c, double *deg_c);

#endif
