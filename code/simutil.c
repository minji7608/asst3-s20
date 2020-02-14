#include "crun.h"

void outmsg(char *fmt, ...) {
    va_list ap;
    bool got_newline = fmt[strlen(fmt)-1] == '\n';
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);
    if (!got_newline)
	fprintf(stderr, "\n");
}


/* Set range of memory locations to zero */
/* Maybe you could use multiple threads ... */
void set_zero(void *buf, size_t len) {
    if (buf == NULL)
	return;
    memset(buf, 0, len);
}


/* Allocate n int's and zero them out. */
int *int_alloc(size_t n) {
    size_t len = n * sizeof(int);
    int *result = (int *) malloc(len);
    set_zero(result, len);
    return result;
}

/* Allocate n doubles's and zero them out. */
double *double_alloc(size_t n) {
    size_t len = n * sizeof(double);
    double *result = (double *) malloc(len);
    set_zero(result, len);
    return result;
}

/* Allocate n random number seeds and zero them out.  */
static random_t *rt_alloc(size_t n) {
    size_t len = n * sizeof(random_t);
    random_t *result = (random_t *) malloc(len);
    set_zero(result, len);
    return result;
}

/* Allocate simulation state */
static state_t *new_rats(graph_t *g, int nrat, int nthread, random_t global_seed) {
    int nnode = g->nnode;
    state_t *s = malloc(sizeof(state_t));
    if (s == NULL) {
	outmsg("Couldn't allocate storage for state\n");
	return NULL;
    }

    s->g = g;
    s->nrat = nrat;
    s->nthread = nthread;
    s->global_seed = global_seed;
    s->load_factor = (double) nrat / nnode;

    /* Compute batch size as max(BATCH_FRACTION * R, sqrt(R)) */
    int rpct = (int) (BATCH_FRACTION * nrat);
    int sroot = (int) sqrt(nrat);
    if (rpct > sroot)
	s->batch_size = rpct;
    else
	s->batch_size = sroot;

    // Allocate data structures
    bool ok = true;
    s->rat_position = int_alloc(nrat);
    ok = ok && s->rat_position != NULL;
    s->rat_seed = rt_alloc(nrat);
    ok = ok && s->rat_seed != NULL;
    s->rat_count = int_alloc(nnode);
    ok = ok && s->rat_count != NULL;

    s->node_weight = double_alloc(nnode);
    ok = ok && s->node_weight != NULL;
    s->sum_weight = double_alloc(g->nnode);
    ok = ok && s->sum_weight != NULL;
    s->neighbor_accum_weight = double_alloc(g->nnode + g->nedge);
    ok = ok && s->neighbor_accum_weight != NULL;
    s->delta_rat_count = int_alloc(nnode);
    ok = ok && s->delta_rat_count != NULL;
    if (!ok) {
	outmsg("Couldn't allocate space for %d rats", nrat);
	return NULL;
    }
    return s;
}

/* Set seed values for the rats.  Maybe you could use multiple threads ... */
static void seed_rats(state_t *s) {
    random_t global_seed = s->global_seed;
    int nrat = s->nrat;
    int r;
    for (r = 0; r < nrat; r++) {
	random_t seeds[2];
	seeds[0] = global_seed;
	seeds[1] = r;
	reseed(&s->rat_seed[r], seeds, 2);
#if DEBUG
	if (r == TAG)
	    outmsg("Rat %d.  Setting seed to %lu\n", r, (unsigned long) s->rat_seed[r]);
#endif
    }
}

/* See whether line of text is a comment */
static inline bool is_comment(char *s) {
    int i;
    int n = strlen(s);
    for (i = 0; i < n; i++) {
	char c = s[i];
	if (!isspace(c))
	    return c == '#';
    }
    return false;
}

/* Read in rat file */
state_t *read_rats(graph_t *g, FILE *infile, int nthread, random_t global_seed) {
    char linebuf[MAXLINE];
    int r, nnode, nid, nrat;

    // Read header information
    while (fgets(linebuf, MAXLINE, infile) != NULL) {
	if (!is_comment(linebuf))
	    break;
    }
    if (sscanf(linebuf, "%d %d", &nnode, &nrat) != 2) {
	outmsg("ERROR. Malformed rat file header (line 1)\n");
	return false;
    }
    if (nnode != g->nnode) {
	outmsg("Graph contains %d nodes, but rat file has %d\n", g->nnode, nnode);
	return NULL;
    }
    
    state_t *s = new_rats(g, nrat, nthread, global_seed);


    for (r = 0; r < nrat; r++) {
	while (fgets(linebuf, MAXLINE, infile) != NULL) {
	    if (!is_comment(linebuf))
		break;
	}
	if (sscanf(linebuf, "%d", &nid) != 1) {
	    outmsg("Error in rat file.  Line %d\n", r+2);
	    return false;
	}
	if (nid < 0 || nid >= nnode) {
	    outmsg("ERROR.  Line %d.  Invalid node number %d\n", r+2, nid);
	    return false;
	}
	s->rat_position[r] = nid;
    }

    seed_rats(s);
#if DEBUG
    outmsg("Loaded %d rats\n", nrat);
    outmsg("Load factor = %f\n", s->load_factor);
#endif
    return s;
}

/* print state of nodes */
void show(state_t *s, bool show_counts) {
    int nid;
    graph_t *g = s->g;
    printf("STEP %d %d %d\n", g->width, g->height, s->nrat);
    if (show_counts) {
	    for (nid = 0; nid < g->nnode; nid++)
		printf("%d\n", s->rat_count[nid]);
    }
    printf("END\n");
}

/* Print final output */
void done() {
    printf("DONE\n");
}

