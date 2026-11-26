REPO_ROOT = $(shell git rev-parse --show-toplevel)/examples/uvmReuse
include $(REPO_ROOT)/include/make/shared.mk

EXTRA_CPP_SRC      +=
EXTRA_CPP_INCLUDES +=
EXTRA_LD_FLAGS     +=
# The leaf's UVM library, which the reused leaf variant packages include.
EXTRA_HDL_INCDIRS  += $(REPO_ROOT)/leaf/uvm

include $(A2C_ROOT)/include/make/a2c-systemc.mk

.PHONY : run run-vl regr_uvm_xcelium

# The testbench is the one the hasTb block uvmReuseChain registers.
run: $(BIN_DIR)/$(BIN)
ifndef VL_DUT
	$(BIN_DIR)/$(BIN) $(HDL_TOP_MODULE)
else
	$(BIN_DIR)/$(BIN) $(HDL_TOP_MODULE) --vlInst $(HDL_TOP_MODULE)
endif

run-vl:
	$(MAKE) all VL_DUT=1
	$(MAKE) run VL_DUT=1

# Farm-only: the UVM regression needs Xcelium (SIMULATOR_INTEGRATION.md
# section 9.7). Both tops build, v8 and v4, each with every DUT.
regr_uvm_xcelium:
	$(A2C_ROOT)/regrLauncher.py --build regr_uvmReuse_uvm_xcelium.json $(REGR_USER_OPTS)

clean::
	$(RM) -rf *.lib++ ucli.key
