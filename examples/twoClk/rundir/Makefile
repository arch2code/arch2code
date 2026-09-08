REPO_ROOT = $(shell git rev-parse --show-toplevel)/examples/twoClk
include $(REPO_ROOT)/include/make/shared.mk

# Include External dependencies in compilation
EXTRA_CPP_SRC      =
EXTRA_CPP_INCLUDES =
EXTRA_LD_FLAGS     =

# Include generated files with names matching '*Includes*.cpp' in SC_GEN_FILES.
EXTRA_O3_CPP_SRC   = $(filter %Includes.cpp %IncludesFW.cpp, $(SC_GEN_FILES))

include $(A2C_ROOT)/include/make/a2c-systemc.mk
include $(A2C_ROOT)/include/make/a2c-agents.mk

.PHONY : run run-vl run-vl-top run-vl-ipSrc run-vl-sink run-vl-slowTick run-vl-slowSink

run: $(BIN_DIR)/$(BIN)
ifndef VL_DUT
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE)
else
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(HDL_TOP_MODULE)
endif

# Verilated sweep of the whole composed DUT and then of each leaf on its own.
# The leaf runs are the ones that carry the twoClkDataIf handshake across the
# SC/RTL boundary - uIpSrc verilated proves RTL -> model, uSink verilated proves
# model -> RTL - because the surviving block model has to see the whole burst
# before it casts its end-of-test vote. uSlowTick/uSlowSink repeat the same
# proof for the clkSlow pair.
run-vl:
	$(MAKE) clean
	$(MAKE) all VL_DUT=1
	$(MAKE) run-vl-top VL_DUT=1
	$(MAKE) run-vl-ipSrc VL_DUT=1
	$(MAKE) run-vl-sink VL_DUT=1
	$(MAKE) run-vl-slowTick VL_DUT=1
	$(MAKE) run-vl-slowSink VL_DUT=1

run-vl-top: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(HDL_TOP_MODULE)

run-vl-ipSrc: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(TB_TOP_MODULE).uIpSrc

run-vl-sink: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(TB_TOP_MODULE).uSink

run-vl-slowTick: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(TB_TOP_MODULE).uSlowTick

run-vl-slowSink: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(TB_TOP_MODULE).uSlowSink
