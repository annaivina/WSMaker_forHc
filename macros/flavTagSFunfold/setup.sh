#!/bin/bash
setupATLAS
asetup AnalysisBase,21.2.95 # or any other release that is reasonable up to date

# set up the PYTHONPATH
THISDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
SCRIPTDIR=$THISDIR"/../../scripts/"
export PYTHONPATH=$SCRIPTDIR:$PYTHONPATH
