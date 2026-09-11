REPO_ROOT = $(shell git rev-parse --show-toplevel)/examples/xprojParam/rtInh
include $(REPO_ROOT)/include/make/shared.mk

# Include External dependencies in compilation
EXTRA_CPP_SRC      =
EXTRA_CPP_INCLUDES =
EXTRA_LD_FLAGS     =
EXTRA_PRJ_SRC_DIRS += $(REPO_ROOT)/fw/src

# This firmware example relies on the arch2code default BSP stubs. The BSP is no
# longer in the default source set, so opt in here: EXTRA_A2C_SRC_DIRS adds both
# the -I include path and the .cpp glob (regRdWr.cpp, fwlog.cpp).
EXTRA_A2C_SRC_DIRS += $(A2C_ROOT)/common/fw/bsp

# Include generated files with names matching '*Includes*.cpp' in SC_GEN_FILES.
EXTRA_O3_CPP_SRC   = $(filter %Includes.cpp %IncludesFW.cpp, $(SC_GEN_FILES))

include $(A2C_ROOT)/include/make/a2c-systemc.mk
include $(A2C_ROOT)/include/make/a2c-agents.mk

.PHONY : run run-vl regr

run: $(BIN_DIR)/$(BIN)
ifndef VL_DUT
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE)
else
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(HDL_TOP_MODULE)
endif

run-vl:
	$(MAKE) clean
	$(MAKE) all VL_DUT=1
	$(MAKE) run VL_DUT=1
