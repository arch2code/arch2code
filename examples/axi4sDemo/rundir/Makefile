REPO_ROOT = $(shell git rev-parse --show-toplevel)/examples/axi4sDemo
include $(REPO_ROOT)/include/make/shared.mk

# Include External dependencies in compilation
EXTRA_CPP_SRC      =
EXTRA_CPP_INCLUDES =
EXTRA_LD_FLAGS     =

# Include generated files with names matching '*Includes*.cpp' in SC_GEN_FILES.
EXTRA_O3_CPP_SRC   = $(filter %Includes.cpp %IncludesFW.cpp, $(SC_GEN_FILES))

include $(A2C_ROOT)/include/make/a2c-systemc.mk

run: $(BIN_DIR)/$(BIN)
ifndef VL_DUT
	$(BIN_DIR)/$(BIN) $(PROJECTNAME)
else
	$(BIN_DIR)/$(BIN) $(PROJECTNAME) --vlInst $(HDL_TOP_MODULE)
endif
