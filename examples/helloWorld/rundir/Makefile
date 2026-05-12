REPO_ROOT = $(shell git rev-parse --show-toplevel)/examples/helloWorld
include $(REPO_ROOT)/include/make/shared.mk

# Include External dependencies in compilation
EXTRA_CPP_SRC      =
EXTRA_CPP_INCLUDES =
EXTRA_LD_FLAGS     =

# Build generated files with names matching '*Includes*.cpp' at -O3 for faster compile.
EXTRA_O3_CPP_SRC   = $(filter %Includes.cpp %IncludesFW.cpp, $(SC_GEN_FILES))

include $(A2C_ROOT)/include/make/a2c-systemc.mk

run: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(PROJECTNAME)
