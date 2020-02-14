#ifndef CRUN_H

/* Defining variable OMP enables use of OMP primitives */
#ifndef OMP
#define OMP 0
#endif


#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdarg.h>
#include <string.h>
#include <ctype.h>
#include <math.h>

#if OMP
#include <omp.h>
#else
#include "fake_omp.h"
#endif

/* Optionally enable debugging routines */
#ifndef DEBUG
#define DEBUG 0
#endif

#if DEBUG
/* Setting TAG to some rat number makes the code track that rat's activity */
#define TAG -1
#endif

#include "rutil.h"
#include "cycletimer.h"
#include "instrument.h"

/*
  Definitions of all constant parameters.  This would be a good place
  to define any constants and options that you use to tune performance
*/

/* What is the maximum line length for reading files */
#define MAXLINE 1024

/* What is the batch size as a fraction of the number of rats */
#define BATCH_FRACTION 0.02

/* What is the base ILF */
#define BASE_ILF 1.75
/* How much can the ILF vary based on relative counts? */
#define ILF_VARIABILITY 0.5


/* What is the crossover between binary and linear search */
#define BINARY_THRESHOLD 4

/* Update modes */
typedef enum { UPDATE_SYNCHRONOUS, UPDATE_BATCH, UPDATE_RAT } update_t;

/* All information needed for graphrat simulation */

/* Parameter abbreviations
   N = number of nodes
   M = number of edge
   R = number of rats
   B = batch size
   T = number of threads
 */


/* Representation of graph */
typedef struct {
    /* General parameters */
    int nnode;
    int nedge;
    int width;
    int height;

    /* Graph structure representation */
    // Adjacency lists.  Includes self edge. Length=M+N.  Combined into single vector
    int *neighbor;
    // Starting index for each adjacency list.  Length=N+1
    int *neighbor_start;
    // Ideal load factor for each node.  (This value gets read from file but is not used.)  Length=N
    double *ilf;
} graph_t;

/* Representation of simulation state */
typedef struct {
    graph_t *g;

    /* Number of rats */
    int nrat;

    /* OMP threads */
    int nthread;

    /* Random seed controlling simulation */
    random_t global_seed;

    /* State representation */
    // Node Id for each rat.  Length=R
    int *rat_position;
    // Rat seeds.  Length = R
    random_t *rat_seed;

    /* Redundant encodings to speed computation */
    // Count of number of rats at each node.  Length = N.
    int *rat_count;
    // Store weights for each node.  Length = N
    double *node_weight;

    /* Computed parameters */
    double load_factor;  // nrat/nnnode
    int batch_size;   // Batch size for batch mode

    /** Mode-specific data structures **/
    // Synchronous and batch mode
    // Memory to store sum of weights for each node's region.  Length = N
    double *sum_weight;
    // Memory to store cummulative weights for each node's region.  Length = M+N
    double *neighbor_accum_weight;

    // Accumulate changes in rat counts in batch mode.  Length = N
    int *delta_rat_count;
} state_t;
    

/*** Functions in graph.c. ***/
graph_t *new_graph(int width, int height, int nedge);

void free_graph();

graph_t *read_graph(FILE *gfile);

#if DEBUG
void show_graph(graph_t *g);
#endif

/*** Functions in simutil.c ***/
/* Print message on stderr */
void outmsg(char *fmt, ...);

/* Allocate and zero arrays of int/double */
int *int_alloc(size_t n);
double *double_alloc(size_t n);

/* Read rat file and initialize simulation state */
state_t *read_rats(graph_t *g, FILE *infile, int nthread, random_t global_seed);

/* Generate done message from simulator */
void done();

/* Print state of simulation */
/* show_counts indicates whether to include counts of rats for each node */
void show(state_t *s, bool show_counts);

/*** Functions in sim.c ***/

/* Run simulation.  Return elapsed time in seconds */
double simulate(state_t *s, int count, update_t update_mode, int dinterval, bool display);

#define CRUN_H
#endif /* CRUN_H */
