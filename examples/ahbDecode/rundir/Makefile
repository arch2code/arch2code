REPO_ROOT = $(shell git rev-parse --show-toplevel)/examples/ahbDecode
include $(REPO_ROOT)/include/make/shared.mk

# Include External dependencies in compilation
EXTRA_CPP_SRC      =
EXTRA_CPP_INCLUDES =
EXTRA_LD_FLAGS     +=

# Include generated files with names matching '*Includes*.cpp' in SC_GEN_FILES.
EXTRA_O3_CPP_SRC   = $(filter %Includes.cpp %IncludesFW.cpp, $(SC_GEN_FILES))

include $(A2C_ROOT)/include/make/a2c-systemc.mk
include $(A2C_ROOT)/include/make/a2c-agents.mk

# Pass RUN_OPTS="--param errorResponses,0" to a build generated without
# fileGeneration regBusErrorResponses.
RUN_OPTS ?=

.PHONY : run run-vl run-vl-ahbSoc run-vl-router run-vl-subSys run-vl-subRouter run-vl-leafA run-vl-leafB run-vl-leafC

run: $(BIN_DIR)/$(BIN)
ifndef VL_DUT
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) $(RUN_OPTS)
else
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(HDL_TOP_MODULE) $(RUN_OPTS)
endif

# Each RTL instance in turn, with models around it
run-vl:
	$(MAKE) clean
	$(MAKE) all VL_DUT=1
	$(MAKE) run-vl-ahbSoc VL_DUT=1
	$(MAKE) run-vl-router VL_DUT=1
	$(MAKE) run-vl-subSys VL_DUT=1
	$(MAKE) run-vl-subRouter VL_DUT=1
	$(MAKE) run-vl-leafA VL_DUT=1
	$(MAKE) run-vl-leafB VL_DUT=1
	$(MAKE) run-vl-leafC VL_DUT=1

run-vl-ahbSoc: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(TB_TOP_MODULE) $(RUN_OPTS)

run-vl-router: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(TB_TOP_MODULE).uRouter $(RUN_OPTS)

run-vl-subSys: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(TB_TOP_MODULE).uSubSys $(RUN_OPTS)

run-vl-subRouter: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(TB_TOP_MODULE).uSubSys.uSubRouter $(RUN_OPTS)

run-vl-leafA: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(TB_TOP_MODULE).uLeafA $(RUN_OPTS)

run-vl-leafB: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(TB_TOP_MODULE).uLeafB $(RUN_OPTS)

run-vl-leafC: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(TB_TOP_MODULE).uSubSys.uLeafC $(RUN_OPTS)
