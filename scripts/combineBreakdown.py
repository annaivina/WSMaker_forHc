#!/usr/bin/env python


import sys, os, re
from argparse import ArgumentParser
from collections import OrderedDict

parser = ArgumentParser()
parser.add_argument("ws")
args = parser.parse_args()

path = f"output/{args.ws}/plots/breakdown"

if not os.path.isdir(path+"/subjobs"):
    print("No subjobs directory exists. Nothing to merge.")
    sys.exit(0)

for root, dirs, files in os.walk(path+"/subjobs"):
    d_merges = {}
    for name in files:
        head, sep, tail = name.partition("_job_")
        d_merges.setdefault(head, []).append(tail)

    d_orderer = {}
    job_pattern = r"(\d+)_of_(.*)"
    for head, lof in d_merges.items():
        for f in lof:
            nr = int(re.search(job_pattern, f).group(1))
            d_orderer[nr] = f

        l_ordered = []
        for key in sorted(d_orderer.keys()):
            l_ordered.append(d_orderer[key])
        d_merges[head] = l_ordered

    print("Going to merge:")
    print(d_merges)


for settings, files in d_merges.items():
    path_out = path+"/"+settings+".txt"
    d_norm_unc = OrderedDict()
    d_frac_unc = OrderedDict()
    print(f"--> merging to {path_out}")
    with open(path_out, 'w') as fout:
        for idx in range(0, len(files)):
            with open( path+"/subjobs/"+settings+"_job_"+files[idx]) as ftmp:
                print("----> {}".format(path+"/subjobs/"+settings+"_job_"+files[idx]))
                contents = ftmp.read()
                head, sep, tail = contents.partition("  Set of nuisance          Impact on error")
                #write settings
                if idx == 0:
                    fout.write(head)

                norm, sep, frac = tail.partition("  Set of nuisance          Fractional impact on error")

                unc_pat = r"(.*?)\+(.*)\-(.*)\+\-(.*)"
                matches = re.finditer(unc_pat, norm)
                for match in matches:
                    if match.group(1) not in d_norm_unc.keys():
                        d_norm_unc[match.group(1)] = [match.group(2), match.group(3), match.group(4)]

                matches = re.finditer(unc_pat, frac)
                for match in matches:
                    if match.group(1) not in d_frac_unc.keys():
                        d_frac_unc[match.group(1)] = [match.group(2), match.group(3), match.group(4)]

        fout.write("Set of nuisance          Impact on error\n")
        fout.write("parameters          \n")
        fout.write("----------------------------------------------------------\n")
        for unc, values in d_norm_unc.items():
            fout.write(unc+"+"+values[0]+"-"+values[1]+"+-"+values[2]+"\n")

        #which ones have not been quad. subtracted?
        with open( path+"/subjobs/"+settings+"_job_"+files[0]) as ftmp:
            contents = ftmp.read()
            h, s, t = contents.partition("Impact on error quadratically subtracted from total, except for:")
            h2,s2,t2 = t.partition("----------------------------------------------------------")

        fout.write("Impact on error quadratically subtracted from total, except for:")
        fout.write(h2)
        fout.write("----------------------------------------------------------\n")
        fout.write("\n")

        fout.write("  Set of nuisance          Fractional impact on error\n")
        fout.write("       parameters          (square of fraction of total)\n")
        fout.write("----------------------------------------------------------\n")

        for unc, values in d_frac_unc.items():
            fout.write(unc+"+"+values[0]+"-"+values[1]+"+-"+values[2]+"\n")

        fout.write("----------------------------------------------------------\n")


