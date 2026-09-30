REPO_ROOT = $(shell git rev-parse --show-toplevel)/unittest/fixtures/regs-container-variant
include $(REPO_ROOT)/include/make/shared.mk

EXTRA_CPP_SRC      =
EXTRA_CPP_INCLUDES =
EXTRA_LD_FLAGS     =

# Include generated files with names matching '*Includes*.cpp' in SC_GEN_FILES.
EXTRA_O3_CPP_SRC   = $(filter %Includes.cpp %IncludesFW.cpp, $(SC_GEN_FILES))

include $(A2C_ROOT)/include/make/a2c-systemc.mk

.PHONY : run

run: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE)
