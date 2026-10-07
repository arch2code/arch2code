REPO_ROOT = $(shell git rev-parse --show-toplevel)/unittest/fixtures/ipparam-only-context
include $(REPO_ROOT)/include/make/shared.mk

EXTRA_CPP_SRC      =
EXTRA_CPP_INCLUDES =
EXTRA_LD_FLAGS     +=

include $(A2C_ROOT)/include/make/a2c-systemc.mk

.PHONY : run

run: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE)
