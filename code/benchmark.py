#!/usr/bin/python

import subprocess
import sys
import os
import os.path
import getopt
import math
import datetime
import random

import rutil

def usage(fname):
    
    ustring = "Usage: %s [-h][-Q][-I] [-b BENCHLIST] [-n NSTEP] [-t T1:T2:..:TK] [-r RUNS] [-i ID] [-f OUTFILE]" % fname
    print ustring
    print "    -h            Print this message"
    print "    -Q            Quick mode: Don't compare with reference solution"
    print "    -I            Instrument simulation activities"
    print "    -b BENCHLIST  Specify which benchmark(s) to perform as substring of 'ABCD'"
    print "    -n NSTEP      Specify number of steps to run simulations"
    print "    -t T1:T2:..TK Specify number of OMP threads as a colon-separated list"
    print "       If > 1, will run crun-omp.  Else will run crun-seq"
    print "    -r RUNS       Set number of times each benchmark is run"
    print "    -i ID         Specify unique ID for distinguishing check files"
    print "    -f OUTFILE    Create output file recording measurements"
    print "         If file name contains field of form XX..X, will replace with ID having that many digits"
    sys.exit(0)

# General information
simProgram = "./crun-seq"
ompSimProgram = "./crun-omp"
refSimProgram = "./crun-soln"
dataDirectory = "./data"

outFile = None

doCheck = True
saveDirectory = "./check"

testFileName = ""
referenceFileName = ""

doInstrument = False

# How many times does each benchmark get run?
runCount = 3

# Grading parameters
pointsPerRun = 16
lowerThreshold = 0.60
upperThreshold = 0.95

# How many mismatched lines warrant detailed report
mismatchLimit = 5

# Graph/rat combinations: testId : (graphFile, ratFile, test name)
benchmarkDict = {
    'A': ('g-180x160-uniA.gph',  'r-180x160-r35.rats', 'uniA'),
    'B': ('g-180x160-uniB.gph',  'r-180x160-r35.rats', 'uniB'),
    'C': ('g-180x160-fracC.gph', 'r-180x160-r35.rats', 'fracC'),
    'D': ('g-180x160-fracD.gph', 'r-180x160-r35.rats', 'fracD'),
    }

graphWidth = 180
graphHeight = 160
loadFactor = 35
defaultSteps = 50
updateMode = "b"
defaultTests = "".join(sorted(benchmarkDict.keys()))

# Latedays machines have 12 cores
threadLimit = 12
host = os.getenv('HOSTNAME')
# Reduce default number of threads on GHC machines
if host is not None and 'ghc' in host:
    threadLimit = 8
defaultThreadCounts = [threadLimit]
defaultSeed = rutil.DEFAULTSEED

uniqueId = ""

def trim(s):
    while len(s) > 0 and s[-1] in '\r\n':
        s = s[:-1]
    return s

def outmsg(s, noreturn = False):
    if len(s) > 0 and s[-1] != '\n' and not noreturn:
        s += "\n"
    sys.stdout.write(s)
    sys.stdout.flush()
    if outFile is not None:
        outFile.write(s)

def testName(testId, stepCount, seed, threadCount):
    name = benchmarkDict[testId][-1]
    root = "%sx%.2d-step%.3d-seed%.3d" % (name, threadCount, stepCount, seed)
    if uniqueId != "":
        root +=  ("-" + uniqueId)
    return root + ".txt"

def dataFile(fname):
    return dataDirectory + '/' + fname

def saveFileName(useRef, testId, stepCount, seed, threadCount):
    return saveDirectory + "/" + ("ref" if useRef else "tst") + testName(testId, stepCount, seed, threadCount)

def checkOutputs(referenceFile, testFile, tname):
    if referenceFile == None or testFile == None:
        return True
    badLines = 0
    lineNumber = 0
    while True:
        rline = referenceFile.readline()
        tline = testFile.readline()
        lineNumber +=1
        if rline == "":
            if tline == "":
                break
            else:
                badLines += 1
                outmsg("Test %s.  Mismatch at line %d.  Reference simulation ended prematurely" % (tname, lineNumber))
                break
        elif tline == "":
            badLines += 1
            outmsg("Test %s.  Mismatch at line %d.  Simulation ended prematurely\n" % (tname, lineNumber))
            break
        rline = trim(rline)
        tline = trim(tline)
        if rline != tline:
            badLines += 1
            if badLines <= mismatchLimit:
                outmsg("Test %s.  Mismatch at line %d.  Expected result:'%s'.  Simulation result:'%s'\n" % (tname, lineNumber, rline, tline))
    referenceFile.close()
    testFile.close()
    if badLines > 0:
        outmsg("%d total mismatches.\n" % (badLines))
    return badLines == 0

def doRun(cmdList, simFileName):
    cmdLine = " ".join(cmdList)
    simFile = subprocess.PIPE
    if simFileName is not None:
        try:
            simFile = open(simFileName, 'w')
        except:
            print "Couldn't open output file '%s'" % simFileName
            return None
    tstart = datetime.datetime.now()
    try:
        outmsg("Running '%s'" % cmdLine)
        simProcess = subprocess.Popen(cmdList, stdout = simFile, stderr = subprocess.PIPE)
        simProcess.wait()
        if simFile != subprocess.PIPE:
            simFile.close()
        returnCode = simProcess.returncode
        # Echo any results printed by simulator on stderr onto stdout
        for line in simProcess.stderr:
            outmsg(line)
    except Exception as e:
        print "Execution of command '%s' failed. %s" % (cmdLine, e)
        if simFile != subprocess.PIPE:
            simFile.close()
        return None
    if returnCode == 0:
        delta = datetime.datetime.now() - tstart
        secs = delta.seconds + 24 * 3600 * delta.days + 1e-6 * delta.microseconds
        if simFile != subprocess.PIPE:
            simFile.close()
        return secs
    else:
        print "Execution of command '%s' gave return code %d" % (cmdLine, returnCode)
        if simFile != subprocess.PIPE:
            simFile.close()
        return None

def bestRun(cmdList, simFileName):
    sofar = 1e6
    for r in range(runCount):
        if runCount > 1:
            outmsg("Run #%d:" % (r+1), noreturn = True)
        secs = doRun(cmdList, simFileName)
        if secs is None:
            return None
        sofar = min(sofar, secs)
    return sofar

def runBenchmark(useRef, testId, stepCount, threadCount):
    global referenceFileName, testFileName
    nodes = graphWidth * graphHeight
    load = loadFactor
    gfname, rfname, tname = benchmarkDict[testId]
    graphFile = dataFile(gfname)
    ratFile = dataFile(rfname)
    params = [tname, str(stepCount)]
    results = params + [str(threadCount)]
    prog = refSimProgram if useRef else simProgram if threadCount == 1 else ompSimProgram
    clist = ["-g", graphFile, "-r", ratFile, "-u", updateMode, "-n", str(stepCount), "-t", str(threadCount)]
    if doInstrument:
        clist += ["-I"]
    simFileName = None
    if not useRef:
        name = testName(testId, stepCount, defaultSeed, threadCount)
        outmsg("+++++++++++++++++ Benchmark %s" % name)
    if doCheck:
        if not os.path.exists(saveDirectory):
            try:
                os.mkdir(saveDirectory)
            except Exception as e:
                outmsg("Couldn't create directory '%s' (%s)" % (saveDirectory, str(e)))
                simFile = subprocess.PIPE
        clist += ["-i", str(stepCount)]
        simFileName = saveFileName(useRef, testId, stepCount, defaultSeed, threadCount)
        if useRef:
            referenceFileName = simFileName
        else:
            testFileName = simFileName
    else:
        clist += ["-q"]
    cmd = [prog] + clist
    cmdLine = " ".join(cmd)
    secs = bestRun(cmd, simFileName)
    if secs is None:
        return None
    else:
        rmoves = (nodes * load) * stepCount
        npm = 1e9 * secs/rmoves
        results.append("%.2f" % secs)
        results.append("%.2f" % npm)
        return results

def score(npm, rnpm):
    if npm == 0.0:
        return 0
    ratio = rnpm/npm
    nscore = 0.0
    if ratio >= upperThreshold:
        nscore = 1.0
    elif ratio >= lowerThreshold:
        nscore = (ratio-lowerThreshold)/(upperThreshold - lowerThreshold)
    return int(math.ceil(nscore * pointsPerRun))

def formatTitle():
    ls = ["Name", "steps", "threads", "secs", "NPM"]
    if doCheck:
        ls += ["BNPM", "Ratio", "Pts"]
    return "\t".join(ls)

def sweep(testList, stepCount, threadCount):
    tcount = 0
    rcount = 0
    sum = 0.0
    refSum = 0.0
    resultList = []
    cresults = None
    totalPoints = 0
    for t in testList:
        ok = True

        results = runBenchmark(False, t, stepCount, threadCount)
        if results is not None and doCheck:
            cresults = runBenchmark(True, t, stepCount, threadCount)
            if referenceFileName != "" and testFileName != "":
                try:
                    rfile = open(referenceFileName, 'r')
                except:
                    rfile = None
                    print "Couldn't open reference simulation output file '%s'" % referenceFileName
                    ok = False
                try:
                    tfile = open(testFileName, 'r')
                except:
                    tfile = None
                    print "Couldn't open test simulation output file '%s'" % testFileName
                    ok = False
                if rfile is not None and tfile is not None:
                    ok = checkOutputs(rfile, tfile, t)
        if results is not None:
            tcount += 1
            npm = float(results[-1])
            sum += npm
            if cresults is not None:
                rcount += 1
                cnpm = float(cresults[-1])
                refSum += cnpm
                ratio = cnpm/npm if npm > 0 else 0
                points = score(npm, cnpm)
                totalPoints += points
                results += [cresults[-1], "%.3f" % ratio, "%d" % points]
            resultList.append(results)
    outmsg("+++++++++++++++++")
    outmsg(formatTitle())
    for r in resultList:
        outmsg("\t".join(r))
    if tcount > 0:
        avg = sum/tcount
        astring = "AVG:\t\t\t\t%.2f" % avg
        if refSum > 0:
            ravg = refSum/rcount
            astring += "\t%.2f" % ravg
        outmsg(astring)
        if doCheck:
            tstring = "TOTAL:\t\t\t\t\t\t\t%d" % totalPoints
            outmsg(tstring)

def generateFileName(template):
    global uniqueId
    myId = ""
    n = len(template)
    ls = []
    for i in range(n):
        c = template[i]
        if c == 'X':
            c = chr(random.randint(ord('0'), ord('9')))
        ls.append(c)
        myId += c
    if uniqueId == "":
        uniqueId = myId
    return "".join(ls) 

def run(name, args):
    global outFile, doCheck
    global uniqueId
    global runCount
    global doInstrument
    nstep = defaultSteps
    testList = list(defaultTests)
    threadCounts = defaultThreadCounts
    optString = "hQIk:b:n:u:t:r:i:f:"
    optlist, args = getopt.getopt(args, optString)
    for (opt, val) in optlist:
        if opt == '-h':
            usage(name)
        elif opt == '-Q':
            doCheck = False
        elif opt == '-I':
            doInstrument = True
        elif opt == '-b':
            testList = list(val)
        elif opt == '-n':
            nstep = int(val)
        elif opt == '-i':
            uniqueId = val
        elif opt == '-f':
            fname = generateFileName(val)
            try:
                outFile = open(fname, "w")
            except Exception as e:
                outFile = None
                outmsg("Couldn't open output file '%s'" % fname)
        elif opt == '-t':
            try:
                threadCounts = [int(s) for s in val.split(":")]
            except:
                print("Thread counts must be given as colon-separated list")
                usage(name)
                return
        elif opt == '-r':
            runCount = int(val)
        else:
            outmsg("Unknown option '%s'" % opt)
            usage(name)
    
    gstart = datetime.datetime.now()
    for t in threadCounts:
        tstart = datetime.datetime.now()
        sweep(testList, nstep, t)
        delta = datetime.datetime.now() - tstart
        secs = delta.seconds + 24 * 3600 * delta.days + 1e-6 * delta.microseconds
        print("Test time for %d threads = %.2f secs." % (t, secs))
    if len(threadCounts) > 1:
        delta = datetime.datetime.now() - gstart
        secs = delta.seconds + 24 * 3600 * delta.days + 1e-6 * delta.microseconds
        print("Overall test time = %.2f secs." % (secs))

if __name__ == "__main__":
    run(sys.argv[0], sys.argv[1:])
