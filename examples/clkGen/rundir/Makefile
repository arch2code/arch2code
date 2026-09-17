REPO_ROOT = $(shell git rev-parse --show-toplevel)/examples/clkGen
include $(REPO_ROOT)/include/make/shared.mk

# Include External dependencies in compilation
EXTRA_CPP_SRC      =
EXTRA_CPP_INCLUDES =
EXTRA_LD_FLAGS     =

# Include generated files with names matching '*Includes*.cpp' in SC_GEN_FILES.
EXTRA_O3_CPP_SRC   = $(filter %Includes.cpp %IncludesFW.cpp, $(SC_GEN_FILES))

include $(A2C_ROOT)/include/make/a2c-systemc.mk
include $(A2C_ROOT)/include/make/a2c-agents.mk

.PHONY : run run-vl run-vl-top run-vl-divider run-vl-consumer

run: $(BIN_DIR)/$(BIN)
ifndef VL_DUT
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE)
else
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(HDL_TOP_MODULE)
endif

# Verilated sweep of the whole composed DUT (proving clkGen's own wrapper
# observes clkDiv rather than generating it) and then of each leaf on its
# own, each proving the model/RTL boundary in the opposite direction.
run-vl:
	$(MAKE) clean
	$(MAKE) all VL_DUT=1
	$(MAKE) run-vl-top VL_DUT=1
	$(MAKE) run-vl-divider VL_DUT=1
	$(MAKE) run-vl-consumer VL_DUT=1

run-vl-top: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(HDL_TOP_MODULE)

run-vl-divider: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(TB_TOP_MODULE).uDivider

run-vl-consumer: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(TB_TOP_MODULE).uConsumer
