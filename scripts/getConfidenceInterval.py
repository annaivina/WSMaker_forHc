"""
A script to extract and print 68% and 95% confidence intervals from 1D likelihood scans.

Author: Philipp Windischhofer
Date:   March 2020
Email:  philipp.windischhofer@cern.ch
"""


from make1DLimitsSummaryPlot import get_1d_CI
from argparse import ArgumentParser

def getConfidenceInterval(infile_path):
    
    CI_68 = get_1d_CI(infile_path, 0.494475)
    CI_95 = get_1d_CI(infile_path, 1.92072)

    print("68% CI")
    print(CI_68)

    print("95% CI")
    print(CI_95)

if __name__ == "__main__":
    parser = ArgumentParser(description = "get CI")
    parser.add_argument("--infile", dest = "infile_path", help = "path to LikelihoodLandscape.root")
    args = vars(parser.parse_args())

    getConfidenceInterval(**args)
