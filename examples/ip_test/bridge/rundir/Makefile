REPO_ROOT = $(shell git rev-parse --show-toplevel)/examples/ip_test/bridge
include $(REPO_ROOT)/include/make/shared.mk

EXTRA_CPP_SRC      =
EXTRA_CPP_INCLUDES =
EXTRA_LD_FLAGS     =
EXTRA_O3_CPP_SRC   = $(filter %Includes.cpp %IncludesFW.cpp, $(SC_GEN_FILES))

# Including the common project puts its cpu block in this project's compile
# closure, and that block uses the arch2code default BSP stubs. The BSP is not in
# the default source set, so opt in here: EXTRA_A2C_SRC_DIRS adds both the -I
# include path and the .cpp glob (regRdWr.cpp, fwlog.cpp).
EXTRA_A2C_SRC_DIRS += $(A2C_ROOT)/common/fw/bsp

include $(A2C_ROOT)/include/make/a2c-systemc.mk
include $(A2C_ROOT)/include/make/a2c-agents.mk

.PHONY : run run-vl run-vl-dut
run: $(BIN_DIR)/$(BIN)
ifndef VL_DUT
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE)
else
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(HDL_TOP_MODULE)
endif

# Cosim: build with the verilated DUT and swap in the reusable ipBridge IP.
# The bridgeStdTop testbench roots its hierarchy at tb, so the ipBridge
# instance is tb.bridgeStdTop.uBridge.
run-vl:
	$(MAKE) clean
	$(MAKE) all VL_DUT=1
	$(MAKE) run-vl-dut VL_DUT=1

run-vl-dut: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst tb.bridgeStdTop.uBridge
