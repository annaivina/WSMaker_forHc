#!/usr/bin/env python


import sys
import ROOT


def main():
    wsname = sys.argv[1]
    mass = "125"
    if len(sys.argv) > 2:
        mass = sys.argv[2]
    f = ROOT.TFile.Open("output/"+wsname+"/workspaces/combined/"+mass+".root")
    ws = f.Get("combined")
    mc = ws.obj("ModelConfig")
    np = mc.GetNuisanceParameters()
    nbNP = np.getSize()
    nbMCstatNP = 0
    nbNormNP = 0

    itr = np.createIterator()
    var = itr.Next()
    dictMCstatMP={}

    while var:
        name = var.GetName()
        if "gamma_stat" in name:
            nbMCstatNP += 1
            reg = name[:name.find("_bin_")]
            reg = reg.split("_",2)[2]
            if reg in dictMCstatMP:
                dictMCstatMP[reg] += 1
            else:
                dictMCstatMP[reg] = 1
        elif "ATLAS_norm" in name:
            nbNormNP += 1
        var = itr.Next()
    nbOtherNP = nbNP - nbMCstatNP - nbNormNP

    print("{:d} NP, among them {:d} are MC stat, {:d} are free normalizations, and {:d} are other \
(systematics)".format(nbNP, nbMCstatNP, nbNormNP, nbOtherNP))
    for k in sorted(dictMCstatMP.keys()):
        print(f"{dictMCstatMP[k]:3d} MC stat NP for region {k}")






if __name__=="__main__":
    main()
