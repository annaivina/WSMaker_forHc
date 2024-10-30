#lxplus only

if [ -z "$1" ]
then
  echo "No argument supplied: Guessing WORKDIR"
  if [[ ${0} == "bash" ]]; then # sourcing this script in the bash shell
    export WORKDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
  else # zsh shell ( at least not bash )
    export WORKDIR="$( cd "$( dirname "$0" )" && pwd )"
  fi
else
  export WORKDIR=$1
fi

export BUILDDIR=${ANALYSISDIR}/build

if [ -z "$2" ]
then
  echo "No argument supplied: setting Blinding"
  export IS_BLINDED=1
else
  export IS_BLINDED=$2
fi

if [ $IS_BLINDED = "1" ];
then
  echo "Blinding the analysis."
else
  echo "Beware the analysis is not blinded"
fi

export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh

lsetup "views LCG_103 x86_64-centos7-gcc11-opt"
# increase stack size - needed for large workspaces
ulimit -S -s unlimited

export LD_LIBRARY_PATH=${ROOTSYS}/lib:${LD_LIBRARY_PATH}
export PATH=${ROOTSYS}/bin:${PATH}
# export PATH=/afs/cern.ch/sw/lcg/external/doxygen/1.8.2/x86_64-slc6-gcc48-opt/bin:$PATH
export PYTHONPATH=${ROOTSYS}/lib:${PYTHONDIR}/lib:${PYTHONPATH}

# include local lib in library path
export LD_LIBRARY_PATH=${BUILDDIR}:${BUILDDIR}/WSMakerCore:${WORKDIR}:${LD_LIBRARY_PATH}
# include local bin in binary path
export PATH=${BUILDDIR}:${WORKDIR}/scripts:${ANALYSISDIR}/scripts:${PATH}

export PYTHONPATH=${ANALYSISDIR}/scripts:${WORKDIR}/scripts:${PYTHONPATH}

mkdir -vp ${BUILDDIR}
mkdir -vp ${ANALYSISDIR}/configs
mkdir -vp ${ANALYSISDIR}/output

echo ""
echo "What to do next:"
echo "Now you must compile the package"
echo "$ cd build && cmake .."
echo "$ make -j5"
