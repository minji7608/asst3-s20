DEBUG=0
CC=gcc
OMP=-fopenmp -DOMP
CFLAGS=-g -O3 -Wall -DDEBUG=$(DEBUG)
#CFLAGS=-g -O3 -Wall -DDEBUG=$(DEBUG) -DDYNAMIC
LDFLAGS= -lm
DDIR = ./data
SOLUTION = crun-soln

CFILES = crun.c graph.c simutil.c sim.c rutil.c cycletimer.c instrument.c
HFILES = crun.h rutil.h cycletimer.h 

all: crun-seq crun-omp


crun-seq: $(CFILES) $(HFILES) fake_omp.h fake_omp.c
	$(CC) $(CFLAGS) -o crun-seq $(CFILES) fake_omp.c $(LDFLAGS)

crun-omp: $(CFILES) $(HFILES)
	$(CC) $(CFLAGS) $(OMP) -o crun-omp $(CFILES) $(LDFLAGS)

demo1: grun.py
	@echo "Running Python simulator with text visualization.  Synchronous mode."
	./grun.py -g data/g-018x012-fracY.gph -r data/r-018x012-c5.rats -n 10 -u s -v a -p 0.5

demo2: grun.py
	@echo "Running Python simulator with heat-map visualization.  Synchronous mode"
	./grun.py -g data/g-036x032-fracZ.gph -r data/r-036x032-c10.rats -u s -n 10 -v h

demo3: crun-seq grun.py
	@echo "Running C simulator using Python simulator as visualizer. Synchronous mode"
	@echo "Note the oscillatory behavior"
	./crun-seq -g data/g-036x032-fracZ.gph -r data/r-036x032-c10.rats -u s -n 20 | ./grun.py -d -v h

demo4: crun-seq grun.py
	@echo "Rat-order mode.  Note the smooth transitions"
	./crun-seq -g data/g-036x032-fracZ.gph -r data/r-036x032-c10.rats -u r -n 20 | ./grun.py -d -v h

demo5: crun-seq grun.py
	@echo "Batch mode. Note the smooth transitions"
	./crun-seq -g data/g-036x032-fracZ.gph -r data/r-036x032-c10.rats -u b -n 20 | ./grun.py -d -v h

demo6: crun-seq grun.py
	@echo "Running on a 180x160 fractal graph"
	./crun-seq -g data/g-180x160-fracC.gph -r data/r-180x160-c35.rats -u b -n 50 | ./grun.py -d -v h

demo7: crun-seq grun.py
	@echo "Running on a 180x160 vertical graph"
	./crun-seq -g data/g-180x160-uniA.gph -r data/r-180x160-c35.rats -u b -n 50 | ./grun.py -d -v h

demo8: crun-seq grun.py
	@echo "Running on a 180x160 grid graph"
	./crun-seq -g data/g-180x160-uniB.gph -r data/r-180x160-c35.rats -u b -n 50 | ./grun.py -d -v h

demo9: crun-seq grun.py
	@echo "Running on a 180x160 fractal graph, with rats initially along diagonal"
	./crun-seq -g data/g-180x160-fracC.gph -r data/r-180x160-d35.rats -u b -n 50 | ./grun.py -d -v h

demo10: crun-seq grun.py
	@echo "Running on a 180x160 fractal graph, with rats initially distributed randomly"
	./crun-seq -g data/g-180x160-fracC.gph -r data/r-180x160-r35.rats -u b -n 50 | ./grun.py -d -v h

demo11: crun-seq
	@echo "Demonstrating instrumentation.  No visualization"
	./crun-seq -g data/g-180x160-fracC.gph -r data/r-180x160-r35.rats -u b -n 50 -I -q


clean:
	rm -f *~ *.pyc
	rm -rf *.dSYM
	rm -rf regression-cache check
	rm -f crun crun-seq crun-omp

