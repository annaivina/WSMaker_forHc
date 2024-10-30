#!/usr/bin/env python


import os
import os.path
import subprocess
import argparse
import fnmatch

# downloaded from pip, shamelessly copied in WSMaker
import tabulate

def main():
    args = parse_input()
    read_files_and_print(args.version_pattern, args.ndigits, args.tabletype)

def parse_input():
    parser = argparse.ArgumentParser(
            description='Pretty printing of significances found in logfiles')

    parser.add_argument('version_pattern', help = 'pattern of versions in which search for signifiances')
    parser.add_argument('--ndigits', help = 'print the values with a limited number of digits',
            default = 6, dest = 'ndigits', type=int)
    parser.add_argument('--tabletype', help = 'format of the table. Either type accepted by tabulate. Can be "simple", "latex".',
            default = "simple", dest = 'tabletype')

    args = parser.parse_args()
    return args

def read_files_and_print(pattern, ndigits, tabletype):
    outputdir = os.path.join(os.environ["ANALYSISDIR"], "output")
    sig_files = list_files(outputdir, pattern)
    values = fill_results_map(sig_files)
    print_significances(values, ndigits, tabletype)


def list_files(outputdir, pattern):
    """List getSig logfiles that match the pattern
    """
    all_ws = os.listdir(outputdir)
    patt_ws = fnmatch.filter(all_ws, pattern)
    all_logfiles = []
    for ws in patt_ws:
        for f in os.listdir(os.path.join(outputdir, ws, "logs")):
            all_logfiles.append(os.path.join(outputdir, ws, "logs", f))
    sig_files = fnmatch.filter(all_logfiles, "*getSig*")
    return sig_files

def fill_results_map(sig_files):
    res = {}
    outputdir = os.path.join(os.environ["ANALYSISDIR"], "output")
    for f in sig_files:
        ws_name = f.replace(outputdir, '').split('/')[0]
        fit_type = ws_name.replace("_012_", "_").replace("_0_", "_").replace("_1_", "_").replace("_2_", "_")
        if not fit_type in res:
            res[fit_type] = [-1, -1, -1, -1]
        if "_012_" in f:
            channel = 3
        elif "_0_" in f:
            channel = 0
        elif "_1_" in f:
            channel = 1
        elif "_2_" in f:
            channel = 2
        else:
            print("ERROR: Impossible to determine channel in file:", f)
        val = float(subprocess.check_output("grep \"Median significance\" "+f+" | cut -d':' -f2",
            shell=True))
        #print(val)
        res[fit_type][channel] = val
    return res

def print_significances(table, ndigits, tabletype):
    print("Expected significances for workspaces matching the input pattern\n")
    #table_as_list = [ [k]+v for k,v in table.items()]
    table_as_list = []
    ws_sorted = []
    for k in sorted(table, compare_ws_names):
        table_as_list.append([k]+table[k])
        ws_sorted.append(k)
    short_names = shorten_ws_names(ws_sorted)
    for i, n in enumerate(short_names):
        table_as_list[i][0] = n
    print(tabulate.tabulate(table_as_list, headers=["Signif", "0", "1", "2", "012"],
        tablefmt=tabletype,
        floatfmt="."+str(ndigits)+"f"
        ))
    pass

def compare_ws_names(ws1, ws2):
    cmp_type = cmp_ws_block(ws1, ws2, ['_StatOnly_', '_MCStat_', '_Systs_'])
    if cmp_type != 0:
        return cmp_type
    cmp_datax = cmp_ws_block(ws1, ws2, ['_mc16a_', '_mc16d_', '_mc16ad_'])
    if cmp_datax != 0:
        return cmp_datax
    return cmp(ws1, ws2)

def cmp_ws_block(ws1, ws2, order_list):
    vals_dict = { v: i for i, v in enumerate(order_list) }
    return cmp(ws_val(ws1, vals_dict), ws_val(ws2, vals_dict))

def ws_val(ws, vals_dict):
    for k in vals_dict:
        if k in ws:
            return vals_dict[k]
    return -1

def shorten_ws_names(names):
    tokenized_names = [n.split('_') for n in names]
    blocks = zip(*tokenized_names)
    tokens_to_remove = []
    for i, b in enumerate(blocks):
        if len(set(b)) == 1: # all tokens equal
            tokens_to_remove.append(i)
    new_blocks = [b for i, b in enumerate(blocks) if i not in tokens_to_remove]
    short_tokenized_names = zip(*new_blocks)
    short_names = ['_'.join(tokens) for tokens in short_tokenized_names]
    return short_names

if __name__ == "__main__":
    main()
