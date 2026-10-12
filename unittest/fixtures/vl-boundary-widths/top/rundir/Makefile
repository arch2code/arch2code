# Create-once scaffold, hand-written so the copy under test resolves through
# FIXTURE_ROOT instead of the surrounding git tree.
include ../include/make/shared.mk

EXTRA_CPP_SRC      =
EXTRA_CPP_INCLUDES =
EXTRA_LD_FLAGS     =

EXTRA_O3_CPP_SRC   = $(filter %Includes.cpp %IncludesFW.cpp, $(SC_GEN_FILES))

# This fixture has no regression file and its testbench runs no tests, so the
# VCS and Xcelium check is the snapshot build itself, one per instantiated top:
#   make USE_VCS=1 vcs_snapshots
#   make USE_XCELIUM=1 xrun_snapshots
DUT_TESTBENCH = vbwTop
DUT_TOPOLOGIES = vbwTop.uDutA:verif vbwTop.uDutC2:verif vbwTop.uDutOut:verif \
	vbwTop.uDutNoRst:verif vbwTop.uDutP0:verif vbwTop.uDutP1:verif vbwTop.uDutP2:verif \
	vbwTop.uWrapQ0.uDutQ:verif vbwTop.uWrapQ1.uDutQ:verif vbwTop.uWrapQ2.uDutQ:verif \
	vbwTop.uLeafA:verif vbwTop.uLeafB:verif vbwTop.uLeafC:verif

include $(A2C_ROOT)/include/make/a2c-systemc.mk
