REPO_ROOT = $(shell git rev-parse --show-toplevel)/examples/xprojParam/rtInh/common
include $(REPO_ROOT)/include/make/shared.mk

# Include External dependencies in compilation
EXTRA_CPP_SRC      =
EXTRA_CPP_INCLUDES =
EXTRA_LD_FLAGS     =

# Include generated files with names matching '*Includes*.cpp' in SC_GEN_FILES.
EXTRA_O3_CPP_SRC   = $(filter %Includes.cpp %IncludesFW.cpp, $(SC_GEN_FILES))

# The cpu block this project owns uses the arch2code default BSP stubs. The BSP is
# no longer in the default source set, so opt in here: EXTRA_A2C_SRC_DIRS adds both
# the -I include path and the .cpp glob (regRdWr.cpp, fwlog.cpp).
EXTRA_A2C_SRC_DIRS += $(A2C_ROOT)/common/fw/bsp

include $(A2C_ROOT)/include/make/a2c-systemc.mk
include $(A2C_ROOT)/include/make/a2c-agents.mk
