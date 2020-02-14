#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

#include "crun.h"

graph_t *new_graph(int width, int height, int nedge) {
    bool ok = true;
    graph_t *g = malloc(sizeof(graph_t));
    if (g == NULL)
	return NULL;
    int nnode = width * height;
    g->nnode = nnode;
    g->nedge = nedge;
    g->width = width;
    g->height = height;
    g->neighbor = calloc(nnode + nedge, sizeof(int));
    ok = ok && g->neighbor != NULL;
    g->neighbor_start = calloc(nnode + 1, sizeof(int));
    ok = ok && g->neighbor_start != NULL;
    g->ilf = calloc(nnode, sizeof(double));
    ok = ok && g->ilf != NULL;
    if (!ok) {
	outmsg("Couldn't allocate graph data structures");
	return NULL;
    }
    return g;
}

void free_graph(graph_t *g) {
    free(g->neighbor);
    free(g->neighbor_start);
    free(g);
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

/* Read in graph file and build graph data structure */
graph_t *read_graph(FILE *infile) {
    char linebuf[MAXLINE];
    int width, height, nnode, nedge;
    int i, hid, tid;
    double ilf;
    int nid, eid;
    int lineno = 0;

    // Read header information
    while (fgets(linebuf, MAXLINE, infile) != NULL) {
	lineno++;
	if (!is_comment(linebuf))
	    break;
    }
    if (sscanf(linebuf, "%d %d %d", &width, &height, &nedge) != 3) {
	outmsg("ERROR. Malformed graph file header (line 1)\n");
	return NULL;
    }
    graph_t *g = new_graph(width, height, nedge);
    if (g == NULL)
	return g;

    nnode = width * height;
    nid = -1;
    // We're going to add self edges, so eid will keep track of all edges.
    eid = 0;
    for (i = 0; i < nnode; i++) {
	while (fgets(linebuf, MAXLINE, infile) != NULL) {
	    lineno++;
	    if (!is_comment(linebuf))
		break;
	}
	if (sscanf(linebuf, "n %lf", &ilf) != 1) {
	    outmsg("Line #%d of graph file malformed.  Expecting node %d\n", lineno, i+1);
	}
	g->ilf[i] = ilf;
    }
    for (i = 0; i < nedge; i++) {
	while (fgets(linebuf, MAXLINE, infile) != NULL) {
	    lineno++;
	    if (!is_comment(linebuf))
		break;
	}
	if (sscanf(linebuf, "e %d %d", &hid, &tid) != 2) {
	    outmsg("Line #%d of graph file malformed.  Expecting edge %d\n", lineno, i+1);
	    return false;
	}
	if (hid < 0 || hid >= nnode) {
	    outmsg("Invalid head index %d on line %d\n", hid, lineno);
	    return false;
	}
	if (tid < 0 || tid >= nnode) {
	    outmsg("Invalid tail index %d on line %d\n", tid, lineno);
	    return false;
	}
	if (hid < nid) {
	    outmsg("Head index %d on line %d out of order\n", hid, lineno);
	    return false;
	    
	}
	// Starting edges for new node(s)
	while (nid < hid) {
	    nid++;
	    g->neighbor_start[nid] = eid;
	    // Self edge
	    g->neighbor[eid++] = nid;
	}
	g->neighbor[eid++] = tid;
    }
    while (nid < nnode-1) {
	// Fill out any isolated nodes
	nid++;
	g->neighbor[eid++] = nid;
    }
    g->neighbor_start[nnode] = eid;
#if DEBUG
    outmsg("Loaded graph with %d nodes and %d edges\n", nnode, nedge);
    show_graph(g);
#endif
    return g;
}

#if DEBUG
void show_graph(graph_t *g) {
    int nid, eid;
    outmsg("Graph\n");
    for (nid = 0; nid < g->nnode; nid++) {
	outmsg("%d:", nid);
	for (eid = g->neighbor_start[nid]; eid < g->neighbor_start[nid+1]; eid++) {
	    outmsg(" %d", g->neighbor[eid]);
	}
	outmsg("\n");
    }
    
}
#endif

