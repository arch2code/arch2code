REPO_ROOT = $(shell git rev-parse --show-toplevel)/unittest/fixtures/inherit-vl-child
include $(REPO_ROOT)/include/make/shared.mk

EXTRA_CPP_SRC      =
EXTRA_CPP_INCLUDES =
EXTRA_LD_FLAGS     =

# Include generated files with names matching '*Includes*.cpp' in SC_GEN_FILES.
EXTRA_O3_CPP_SRC   = $(filter %Includes.cpp %IncludesFW.cpp, $(SC_GEN_FILES))

include $(A2C_ROOT)/include/make/a2c-systemc.mk

.PHONY : run run-vl-def run-vl-alt

run: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE)

# Swap the verilated leaf into the DEFAULT container instance. Exactly one
# instance is verilated per run, so the two container variants are two runs.
# uLeafB is the LAST leaf in the chain, so the algorithm and width the checker
# reads back are the ones the VERILATED leaf stamped; swapping uLeafA instead
# would let its downstream model twin overwrite both.
run-vl-def: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst tb.$(TB_TOP_MODULE).uWrap.uContDef.uLeafB

# The same swap under the `alt` container instance, whose Config carries both a
# different algorithm and a different payload width.
run-vl-alt: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst tb.$(TB_TOP_MODULE).uWrap.uContAlt.uLeafB
