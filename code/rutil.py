# Implementation of math and random number functions for rat simulation
#
# The random number generator isn't especially good, but it provides
# control over the seed, and it can be easily translated into other
# languages.

# CONSTANTS
# These are the parameters used in the C++ minstd_rand random number
# generator It is based on a class of linear congruential generators
# due to D. H. Lehmer The parameters were suggested by Stephen K. Park
# and Keith W. Miller, and Paul K. Stockmeyer in CACM, July 1988.

GROUPSIZE = 2147483647 # 2^31 - 1, a prime number
MVAL = 48271
VVAL = 16807
INITSEED = 418
DEFAULTSEED = 618

import math

# Some installations don't support numpy library.
# Import them only if needed

specialImported = False

def importSpecial():
    global specialImported, np
    if not specialImported:
        import numpy as np
    specialImported = True

class RNG:
    seed = INITSEED

    # Initialize with either single int as seed, or with seqence of ints
    def __init__(self, seeds = []):
        self.reseed(seeds)

    def reseed(self, seeds = []):
        self.seed = INITSEED
        for s in seeds:
            self.next(s)

    def next(self, x = 0):
        val = ((x+1) * VVAL + self.seed * MVAL) % GROUPSIZE
        self.seed = val
        return val

    # Return random float, distributed uniformly in interval [0, upperLimit)
    def randFloat(self, upperLimit = 1.0):
        oldseed = self.seed
        val = self.next()
        rval = (float(val)/GROUPSIZE) * upperLimit
        return rval

    # Convert number on scale [0, 1.0] to one between two bounds
    # but exponentially distributed
    def expandExp(self, value, lowerLimit = 0.5, upperLimit = 2.0):
        lrange = math.log(upperLimit / lowerLimit)
        evalue = value * lrange
        return math.exp(evalue) * lowerLimit

    # Return random float, distributed exponentially in interval [lowerLimit, upperLimit)
    def randExpFloat(self, lowerLimit = 0.5, upperLimit = 2.0):
        return self.expandExp(self.randFloat(1.0))

    # Return random integer, distributed uniformly in interval [lower, upper]
    def randInt(self, lower, upper):
        rval = self.randFloat()
        return lower + int(rval * (upper + 1 - lower))

    def randElement(self, ls):
        idx = self.randInt(0, len(ls)-1)
        return ls[idx]

    # Choose maxSample elements (without replacement) from sequence at random
    # and return as list.
    def sample(self, seq, maxSample):
        if len(seq) <= maxSample:
            return seq
        result = [0] * maxSample
        swaps = [0] * maxSample
        for i in range(maxSample):
            w = self.randFloat()
            idx = i + int(w * float(len(seq)-i))
            swaps[i] = idx
            result[i] = seq[idx]
            seq[idx], seq[i] = seq[i], seq[idx]
        # Use list of swaps to restore input sequence
        for i in range(maxSample-1, -1, -1):
            idx = swaps[i]
            seq[idx], seq[i] = seq[i], seq[idx]
        return result

    # Return list containing all elements of seq in random order
    # Much faster than using sample()
    def permute(self, seq):
        if len(seq) == 0:
            return seq
        importSpecial()
        n = len(seq)
        a = np.array(range(n))
        while (n > 1):
            idx = self.randInt(0, n-1)
            a[idx], a[n-1] = a[n-1], a[idx]
            n -= 1
        result = []
        for i in a:
            result.append(seq[i])
        return result

    # Given a sequence of non-negative weights, choose
    # number between 0 and n-1 based on those weights
    # where n = len(weights)
    def weightedIndex(self, weights):
        sum = reduce(lambda x, y: x + y, weights)
        cval = self.randFloat(sum)
        psum = 0.0
        for idx in range(len(weights)):
            psum += weights[idx]
            if cval < psum:
                return idx


# Parameters for computing the weights that guide next-move selection
COEFF = 0.4
OPTVAL = 1.5
BLIMIT = 1.0
L2E = math.log(math.e, 2)

def mweight(val, optval = OPTVAL):

    arg = 1.0 + COEFF * (val - optval)
    if arg <= 0.0:
        return 0.0
    log = math.log(arg) * L2E
    denom = 1.0 + log * log
    return 1.0/denom

# Compute imbalance between local and remote values
# Result < 0 when lcount > rcount and > 0 when lcount < rcount
def imbalance(lcount, rcount):
    if lcount == 0 and rcount == 0:
        return 0
    sl = math.sqrt(float(lcount))
    sr = math.sqrt(float(rcount))
    return (sr-sl)/(sr+sl)

# Given list of values 
# (each of which is the number of rats at a node divided by the load factor)
# compute weights for nodes and select index of one
def chooseMove(rng, vals, optvals):
    weights = [mweight(vals[i],optvals[i]) for i in range(len(vals))]
    return rng.weightedIndex(weights)
