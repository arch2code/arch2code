# Create-once scaffold, hand-written so the copy under test resolves through
# FIXTURE_ROOT instead of the surrounding git tree.
include ../include/make/shared.mk

EXTRA_CPP_SRC      =
EXTRA_CPP_INCLUDES =
EXTRA_LD_FLAGS     =

EXTRA_O3_CPP_SRC   = $(filter %Includes.cpp %IncludesFW.cpp, $(SC_GEN_FILES))

include $(A2C_ROOT)/include/make/a2c-systemc.mk

.PHONY : run

run: $(BIN_DIR)/$(BIN)
ifndef VL_DUT
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE)
else
	$(BIN_DIR)/$(BIN) $(TB_TOP_MODULE) --vlInst $(HDL_TOP_MODULE)
endif
