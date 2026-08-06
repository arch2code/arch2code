REPO_ROOT = $(shell git rev-parse --show-toplevel)/examples/apbDecode
include $(REPO_ROOT)/include/make/shared.mk

# Include External dependencies in compilation
EXTRA_CPP_SRC      =
EXTRA_CPP_INCLUDES =
EXTRA_LD_FLAGS     =

# Include generated files with names matching '*Includes*.cpp' in SC_GEN_FILES.
EXTRA_O3_CPP_SRC   = $(filter %Includes.cpp %IncludesFW.cpp, $(SC_GEN_FILES))

include $(A2C_ROOT)/include/make/a2c-systemc.mk
include $(A2C_ROOT)/include/make/a2c-agents.mk

.PHONY : run run-vl run-vl-blockA run-vl-blockB run-vl-apbDecode run-vl-someRapper regr

regr:
	$(A2C_ROOT)/regrLauncher.py --build -j8 regr_apbDecode.json $(REGR_USER_OPTS)

run: $(BIN_DIR)/$(BIN)
ifndef VL_DUT
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE)
else
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(HDL_TOP_MODULE)
endif

run-vl:
	$(MAKE) clean
	$(MAKE) all VL_DUT=1
	$(MAKE) run-vl-someRapper
	$(MAKE) run-vl-apbDecode
	$(MAKE) run-vl-blockA
	$(MAKE) run-vl-blockB

run-vl-someRapper: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(TB_TOP_MODULE)

run-vl-apbDecode: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(TB_TOP_MODULE).uAPBDecode

run-vl-blockA: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(TB_TOP_MODULE).uBlockA

run-vl-blockB: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(TB_TOP_MODULE).uBlockB
