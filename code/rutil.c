/*
  C library implementing math functions for rat simulator.
  Provides same functionality as Python code in rutil.py
*/

#include "rutil.h"
#include <stdio.h>

/* Standard parameters */
#define GROUPSIZE 2147483647
#define MVAL  48271
#define VVAL  16807
#define INITSEED  418


static inline random_t rnext(random_t *seedp, random_t x) {
    uint64_t s = (uint64_t) *seedp;
    uint64_t xlong = (uint64_t) x;
    random_t val = ((xlong+1) * VVAL + s * MVAL) % GROUPSIZE;
    *seedp = (random_t) val;
    return val;
}

/* Reinitialize seed based on list of seeds, where list has length len */
void reseed(random_t *seedp, random_t seed_list[], size_t len) {
    *seedp = INITSEED;
    size_t i;
    for (i = 0; i < len; i++)
	rnext(seedp, seed_list[i]);
}

/* Generate double in range [0.0, upperlimit) */
double next_random_float(random_t *seedp, double upperlimit) {
    random_t val = rnext(seedp, 0);
    return ((double) val / (double) GROUPSIZE) * upperlimit;
}

/* Select sample of size up to maxSample (without replacement) from list or size populationCount */
/* Store result in array dest.  Array scratch must have space for sampleCount entries. */
/* Returns minimum of populationCount and maxSample */
int sample(random_t *seedp, int *seq, int populationCount, int maxSample, int *dest, int *scratch) {
    int i, idx, tmp;
    if (populationCount <= maxSample) {
	for (i = 0; i < populationCount; i++)
	    dest[i] = seq[i];
	return populationCount;
    }
    for (i = 0; i < maxSample; i++) {
	double w = next_random_float(seedp, 1.0);
	idx = i + (int) (w * (double) (populationCount-i));
	scratch[i] = idx;
	tmp = seq[idx];
	seq[idx] = seq[i];
	seq[i] = tmp;
	dest[i] = tmp;
    }
    for (i = maxSample-1; i >= 0; i--) {
	idx = scratch[i];
	tmp = seq[idx];
	seq[idx] = seq[i];
	seq[i] = tmp;
    }
    return maxSample;
}


/* Parameters for computing weights that guide next-move selection */
#define COEFF 0.4
#define OPTVAL 1.5

double mweight(double val, double optval) {
    double arg = 1.0 + COEFF * (val - optval);
    double lg = log(arg) * M_LOG2E;
    double denom = 1.0 + lg * lg;
    return 1.0/denom;
}

/* Compute imbalance between local and remote values */
/* Result < 0 when lcount > rcount and > 0 when lcount < rcount */
double imbalance(int lcount, int rcount) {
    if (lcount == 0 && rcount == 0)
	return 0.0;
    double sl = sqrt((double) lcount);
    double sr = sqrt((double) rcount);
    return (sr-sl)/(sr+sl);
}
