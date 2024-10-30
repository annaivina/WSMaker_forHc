################################################################################
# Build configuration for WSMaker
################################################################################

# Set the minimum required CMake version:
cmake_minimum_required( VERSION 3.4 FATAL_ERROR )

project(wsmaker)

# You need to tell CMake where to find the ROOT installation. This can be done in a number of ways:
#   - ROOT built with classic configure/make use the provided $ROOTSYS/etc/cmake/FindROOT.cmake
#   - ROOT built with CMake. Add in CMAKE_PREFIX_PATH the installation prefix for ROOT
list(APPEND CMAKE_PREFIX_PATH $ENV{ROOTSYS})

#---Locate the ROOT package and defines a number of variables (e.g. ROOT_INCLUDE_DIRS)
find_package(ROOT REQUIRED COMPONENTS RIO EG Minuit RooFit RooFitCore RooStats HistFactory)

#---Define useful ROOT functions and macros (e.g. ROOT_GENERATE_DICTIONARY)
include(${ROOT_USE_FILE})

#---Add TranformTool to the fun
add_subdirectory (TransformTool)

include_directories(${CMAKE_CURRENT_SOURCE_DIR}/WSMaker ${CMAKE_CURRENT_SOURCE_DIR}/TransformTool)
file(GLOB headers "WSMaker/*.hpp" "WSMaker/*.h")
ROOT_GENERATE_DICTIONARY(G__WSMaker ${headers} LINKDEF src/Linkdef.h)

#---Create a shared library with geneated dictionary
file(GLOB sources "src/*.cpp")
add_library(WSMaker SHARED ${sources} G__WSMaker.cxx)
target_link_libraries(WSMaker ${ROOT_LIBRARIES})

#---Compile the ROOT macros
list(APPEND fit_macros_sources "FitCrossCheckForLimits" "LikelihoodLandscape" "newGetMuHat" "muHatModes" "runAsymptoticsCLs" "runSig" "macros/runPulls" "macros/runBreakdown" "macros/drawPlot_pulls")

foreach(cur_source ${fit_macros_sources})

    set(cur_in_file $ENV{WORKDIR}/${cur_source}.C)
    set(cur_out_file $ENV{WORKDIR}/${cur_source}_C.so)

    add_custom_command(OUTPUT ${cur_out_file}
        COMMAND sh $ENV{WORKDIR}/compile_macro.sh ${cur_in_file}
        DEPENDS ${cur_in_file}
    )

    list(APPEND fit_macros_libs ${cur_out_file})

endforeach(cur_source)

add_custom_target(FitTools
    DEPENDS ${fit_macros_libs}
)

add_dependencies(WSMaker FitTools)
