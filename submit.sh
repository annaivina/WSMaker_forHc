#!/bin/bash
#PBS -q gpu
#PBS -N chtest
#PBS -l io=5
#PBS -l mem=1gb
#PBS -o output.log
#PBS -e job_error.log
#PBS -l ncpus=4
#PBS -l ngpus=1
#PBS -l walltime=04:00:00

# Change to job submission directory
cd /storage/agrp/annai/Hc_Yukawa_Analysis/NPs/New/WSMaker

# Load any necessary modules or source environment
source setup_new.sh
export WORKDIR="/srv01/agrp/annai/annai/Hc_Yukawa_Analysis/NPs/New/WSMaker"
# Execute the script
#python scripts/runLikelihoodLandscape.py --infile_path data_new_May2024.root --outputdir test_out_2mu_den100_subjobs400_strat22_eps001_NewData --WorkspaceName workspace --ModelConfigName modelSB --ObsDataName data --algs 3  --subjobs 300

python scripts/runLikelihoodLandscape.py --infile_path 2mu_newbug.root --outputdir test_out_2mu_den100_subjobs400_strat22_eps001_NewData_newbug --WorkspaceName workspace --ModelConfigName modelSB --ObsDataName data --algs 3  --subjobs 300
