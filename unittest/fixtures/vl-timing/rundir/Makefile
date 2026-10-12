REPO_ROOT = $(shell git rev-parse --show-toplevel)/unittest/fixtures/vl-timing
include $(REPO_ROOT)/include/make/shared.mk

include $(A2C_ROOT)/include/make/a2c-systemc.mk

.PHONY : run run-vl

run: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE)

run-vl: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst tb.$(TB_TOP_MODULE).uSrc
