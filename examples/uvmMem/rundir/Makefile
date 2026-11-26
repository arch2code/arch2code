REPO_ROOT = $(shell git rev-parse --show-toplevel)/examples/uvmMem
include $(REPO_ROOT)/include/make/shared.mk

EXTRA_CPP_SRC      +=
EXTRA_CPP_INCLUDES +=
EXTRA_LD_FLAGS     +=

include $(A2C_ROOT)/include/make/a2c-systemc.mk

.PHONY : run run-vl regr_uvm_xcelium regr_uvm_vcs

# The testbench is the one the hasTb block uvmMem registers.
run: $(BIN_DIR)/$(BIN)
ifndef VL_DUT
	$(BIN_DIR)/$(BIN) $(PROJECTNAME)
else
	$(BIN_DIR)/$(BIN) $(PROJECTNAME) --vlInst $(HDL_TOP_MODULE)
endif

run-vl:
	$(MAKE) all VL_DUT=1
	$(MAKE) run VL_DUT=1

# Farm-only: the UVM regressions need Xcelium or VCS (SIMULATOR_INTEGRATION.md
# section 9.7). Each build command sets USE_UVM and the vendor.
regr_uvm_xcelium:
	$(A2C_ROOT)/regrLauncher.py --build regr_uvmMem_uvm_xcelium.json $(REGR_USER_OPTS)

regr_uvm_vcs:
	$(A2C_ROOT)/regrLauncher.py --build regr_uvmMem_uvm_vcs.json $(REGR_USER_OPTS)

clean::
	$(RM) -rf *.lib++ ucli.key
