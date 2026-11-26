REPO_ROOT = $(shell git rev-parse --show-toplevel)/examples/uvmReuse/leaf
include $(REPO_ROOT)/include/make/shared.mk

EXTRA_CPP_SRC      +=
EXTRA_CPP_INCLUDES +=
EXTRA_LD_FLAGS     +=
# The leaf's UVM library (uvmReuseLeaf_lib.svh), which its variant packages
# include.
EXTRA_HDL_INCDIRS  += $(REPO_ROOT)/uvm

include $(A2C_ROOT)/include/make/a2c-systemc.mk

.PHONY : regr_uvm_xcelium

# Farm-only: the UVM regression needs Xcelium (SIMULATOR_INTEGRATION.md
# section 9.7). The project runs no SystemC test of its own.
regr_uvm_xcelium:
	$(A2C_ROOT)/regrLauncher.py --build regr_uvmReuseLeaf_uvm_xcelium.json $(REGR_USER_OPTS)

clean::
	$(RM) -rf *.lib++ ucli.key
