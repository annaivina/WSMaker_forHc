#!/bin/bash

echo "gROOT->ProcessLine(\".L ${1}++\"); gSystem->Exit(0)" | root -l -b
