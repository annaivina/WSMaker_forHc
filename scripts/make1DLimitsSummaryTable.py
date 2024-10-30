"""
Fetches the same information as "make1DLimitsSummaryPlot.py", but puts it into a Latex-compatible table instead.

Author: Philipp Windischhofer
Date:   March 2020
Email:  philipp.windischhofer@cern.ch
"""


import os
from argparse import ArgumentParser
from make1DLimitsSummaryPlot import get_1d_CI
from analysisPlottingConfig import Config
from argparse import ArgumentParser

def make1DLimitsSummaryTable(run_dirs_linear, run_dirs_quadratic):

    plotconf = Config(options = [])
    
    def read_CIs(run_dirs, CL, exp):
        CIs = {}
        for run_dir in run_dirs:
            
            # need to load both expected and observed NLL scan results
            if exp:
                scan_result = os.path.join(run_dir, "LikelihoodLandscape", "Asimov", "LikelihoodLandscape_out.root")
            else:
                scan_result = os.path.join(run_dir, "LikelihoodLandscape", "Data", "LikelihoodLandscape_out.root")

            scan_result = run_dir

            # get the 1D confidence intervals to show on the plots
            operator, CI = get_1d_CI(scan_result, CL)
            CIs[operator] = CI

        return CIs

    def to_string(array):
        stringarray = [f"{cur:.2g}" for cur in list(array)]
        retstring = "[" + ", ".join(stringarray) + "]"
        return retstring

    def get_CI_string(library, operator):
        if operator in library:
            CI_string = r" $\cup$ ".join(map(to_string, library[operator]))
        else:
            CI_string = " --- "
        
        return CI_string

    def print_table_header():
        print("\begin{tabular}{c|c|c|c|c}")
        print(" Wilson          & \\multicolumn{2}{c}{linear}   & \\multicolumn{2}{c}{linear + quadratic} \\\\ ")
        print(" coefficient     & expected        & observed        & expected           & observed          \\\\\\hline\\hline ")

    def print_table_row(wilson_coeff, CI_linear_exp, CI_linear_obs, CI_quadratic_exp, CI_quadratic_obs):
        print(f"${wilson_coeff}$    &   {CI_linear_exp}   &   {CI_linear_obs}   &   {CI_quadratic_exp}   &   {CI_quadratic_obs}   \\\\\\hline")

    def print_table_footer():
        print(r"\end{tabular}")

    # read the CIs from the individual fit results
    CIs_68_linear_obs = read_CIs(run_dirs_linear, 0.494475, exp = False)
    CIs_68_linear_exp = read_CIs(run_dirs_linear, 0.494475, exp = True)
    CIs_95_linear_obs = read_CIs(run_dirs_linear, 1.92072, exp = False)
    CIs_95_linear_exp = read_CIs(run_dirs_linear, 1.92072, exp = True)

    CIs_68_quadratic_obs = read_CIs(run_dirs_quadratic, 0.494475, exp = False)
    CIs_68_quadratic_exp = read_CIs(run_dirs_quadratic, 0.494475, exp = True)
    CIs_95_quadratic_obs = read_CIs(run_dirs_quadratic, 1.92072, exp = False)
    CIs_95_quadratic_exp = read_CIs(run_dirs_quadratic, 1.92072, exp = True)
    
    operator_order_68 = list(set(CIs_68_linear_obs.keys()))
    operator_order_95 = list(set(CIs_95_linear_obs.keys()))

    # generate the table for 68% CIs
    print("===========================================")
    print(" Table for 68% CL limits")
    print("===========================================")
    print_table_header()
    for cur_operator in operator_order_68:

        cur_operator_name = plotconf.EFT_operator_labels[cur_operator]

        CI_linear_obs = get_CI_string(CIs_68_linear_obs, cur_operator)
        CI_quadratic_obs = get_CI_string(CIs_68_quadratic_obs, cur_operator)

        CI_linear_exp = get_CI_string(CIs_68_linear_exp, cur_operator)
        CI_quadratic_exp = get_CI_string(CIs_68_quadratic_exp, cur_operator)

        print_table_row(cur_operator_name, CI_linear_exp, CI_linear_obs, CI_quadratic_exp, CI_quadratic_obs)
    print_table_footer()
    print("===========================================")

    # generate the table for 95% CIs
    print("===========================================")
    print(" Table for 95% CL limits")
    print("===========================================")
    print_table_header()
    for cur_operator in operator_order_95:

        cur_operator_name = plotconf.EFT_operator_labels[cur_operator]

        CI_linear_obs = get_CI_string(CIs_95_linear_obs, cur_operator)
        CI_quadratic_obs = get_CI_string(CIs_95_quadratic_obs, cur_operator)

        CI_linear_exp = get_CI_string(CIs_95_linear_exp, cur_operator)
        CI_quadratic_exp = get_CI_string(CIs_95_quadratic_exp, cur_operator)

        print_table_row(cur_operator_name, CI_linear_exp, CI_linear_obs, CI_quadratic_exp, CI_quadratic_obs)
    print_table_footer()
    print("===========================================")

if __name__ == "__main__":
    parser = ArgumentParser(description = "make summary table")
    parser.add_argument("--run_dirs_linear", nargs = '+', dest = "run_dirs_linear", help = "path to the individual fit directories")
    parser.add_argument("--run_dirs_quadratic", nargs = '+', dest = "run_dirs_quadratic", help = "path to the individual fit directories")
    args = vars(parser.parse_args())

    make1DLimitsSummaryTable(**args)

