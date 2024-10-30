import glob, os, sys
import subprocess
from ROOT import *
from glob import *
import time
import math

# this script calculates the compatibility between two \mu values obtained on same dataset
# first argument is the first \mu_1
# second argument is the second \mu_2
# for which we want to compute the statistical compatibility
# third argument has to be the difference in the number of degrees of freedom (POIs) between the two fits whose results are \mu_1 and \mu_2

if len(sys.argv)!=4:
    print(" NOT ENOUGH parameters provided ")
    print(" python GetCompatibility 1M-LLR, 2M-LLR, nDGF ")
    sys.exit()

singLLR=float(sys.argv[1])
multLLR=float(sys.argv[2])
nDGF   =int(sys.argv[3])

compatibility=TMath.Prob(2*(singLLR-multLLR),nDGF)
print("Compatibility is: "+str(compatibility*100)+" % ")


