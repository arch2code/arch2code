REPO_ROOT = $(shell git rev-parse --show-toplevel)/unittest/fixtures/hier-layout
include $(REPO_ROOT)/include/make/shared.mk

# Include External dependencies in compilation
EXTRA_CPP_SRC      =
EXTRA_CPP_INCLUDES =
EXTRA_LD_FLAGS     =

# Include generated files with names matching '*Includes*.cpp' in SC_GEN_FILES.
EXTRA_O3_CPP_SRC   = $(filter %Includes.cpp %IncludesFW.cpp, $(SC_GEN_FILES))

include $(A2C_ROOT)/include/make/a2c-systemc.mk

# Run the block-level testbench by name (the core DUT carries hasTb: true, so
# its tb config self-registers as "core"). hier_tb is the root container only.
run: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) core
