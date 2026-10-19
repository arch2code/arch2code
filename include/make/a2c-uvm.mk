# UVM testbench flow, USE_UVM=1 with USE_VCS=1 or USE_XCELIUM=1. The SystemC
# side runs the block's generated <block>_uvm testbench, which instantiates
# one UVM testbench top; that top drives the block's model or, with
# UVM_DUT=rtl, its RTL. Each top and DUT is its own snapshot,
# run_uvm_<top>_<dut>. a2c-systemc.mk includes this file before it names the
# snapshot and collects the sources; the vendor recipe items are under
# USE_UVM in a2c-vcs.mk and a2c-xrun.mk.
#
#   UVM_TOP         the top's stem, <block>_<variant>; defaults to the top at
#                   the variant of HDL_TOP_MODULE's DUT-top wrapper
#   UVM_DUT         model or rtl; defaults to model, or to rtl for a block
#                   with no model
#   UVM_TEST        the +UVM_TESTNAME the run script passes when the test
#                   names none
#   UVM_TOPOLOGIES  what uvm_snapshots builds, <top>:<dut>[,<dut>]... per top;
#                   defaults to UVM_TOP with each DUT its block has

ifeq ($(USE_VCS)$(USE_XCELIUM),)
$(error USE_UVM=1 needs USE_VCS=1 or USE_XCELIUM=1: the UVM flow runs on VCS and Xcelium only)
endif
ifeq ($(VL_DUT),)
$(error USE_UVM=1 needs VL_DUT=1: VL_DUT compiles the RTL, which every UVM snapshot needs for its rtl DUT)
endif

UVM_TOP ?= $(A2C_UVM_DEFAULT_TOP_$(HDL_TOP_MODULE))
UVM_TB_TOP := $(A2C_UVM_TB_TOP_$(UVM_TOP))
UVM_DUT ?= $(firstword $(A2C_UVM_DUTS_$(UVM_TB_TOP)))
ifeq ($(UVM_DUT),both)
$(error UVM_DUT=both, the model and the RTL in one snapshot, is not supported yet; use model or rtl)
endif
UVM_TEST ?=
UVM_TOPOLOGIES ?= $(UVM_TOP):$(subst $(space),$(comma),$(A2C_UVM_DUTS_$(UVM_TB_TOP)))

# Checked when gen runs rather than at parse time, because a missing or stale
# manifest is rebuilt only after the first parse.
gen: uvm-top-check
.PHONY: uvm-top-check
uvm-top-check:
	$(if $(UVM_TB_TOP),,$(error UVM_TOP '$(UVM_TOP)' names no UVM testbench top; set it to one of: $(A2C_UVM_TOP_STEMS)))
	$(if $(filter $(UVM_DUT),$(A2C_UVM_DUTS_$(UVM_TB_TOP))),,$(error UVM_DUT must be one of $(A2C_UVM_DUTS_$(UVM_TB_TOP)) for UVM_TOP $(UVM_TOP), not '$(UVM_DUT)'))

VL_INST :=
DUT_TOPOLOGY := uvm_$(UVM_TOP)_$(UVM_DUT)
DUT_ELAB_ARGS := $(A2C_UVM_TESTBENCH_$(UVM_TB_TOP)) --uvmDut $(UVM_DUT) --uvmTop $(UVM_TOP)

# The clock interface, a2c_uvm_pkg and the agent packages, then a builder
# layer's agent packages from A2C_LAYER_UVM_F_FILES, then the top's variant
# package, the test package that imports it, and the testbench module, whose
# generated header imports the test package. A2C_SV_FILES follows rtl.f, so
# they compile after the project packages they import. A layer list holds
# file paths only, each relative to the list's own directory.
A2C_UVM_F := $(A2C_ROOT)/common/systemVerilog/uvm/a2c_uvm.f
A2C_UVM_LIB_SV := $(wildcard $(A2C_ROOT)/common/systemVerilog/uvm/*.sv $(A2C_ROOT)/interfaces/*/*_uvm_pkg.sv)
A2C_LAYER_UVM_SV := $(foreach f,$(A2C_LAYER_UVM_F_FILES),$(addprefix $(dir $(f)),$(file < $(f))))
A2C_UVM_SV_FILES := $(A2C_UVM_PKG_SV_$(UVM_TB_TOP)) $(A2C_UVM_TEST_SV_$(UVM_TB_TOP)) $(A2C_UVM_TB_SV_$(UVM_TB_TOP))
A2C_UVM_HDL_DEFINES := A2C_UVM_PKG=$(A2C_UVM_PKG_$(UVM_TB_TOP)) $(if $(filter rtl,$(UVM_DUT)),A2C_UVM_RTL_DUT)
A2C_SV_FILES += $(A2C_UVM_SV_FILES)
A2C_HDL_ARGS += -F $(A2C_UVM_F) $(addprefix -F ,$(A2C_LAYER_UVM_F_FILES)) $(addprefix +define+,$(A2C_UVM_HDL_DEFINES))
A2C_HDL_DEPS += $(A2C_UVM_F) $(A2C_LAYER_UVM_F_FILES) $(A2C_LAYER_UVM_SV) $(A2C_UVM_LIB_SV) $(A2C_UVM_SV_FILES)

# The generated wrapper, testbench config and registrar.
PRJ_SRC_DIRS += $(A2C_UVM_SRC_DIRS)
ifdef USE_VCS
A2C_SRC_DIRS += $(A2C_ROOT)/common/systemc/uvm
endif

# One build per top and DUT, in turn: the snapshots link the same C++ objects,
# which the first builds, and under VCS they also share AN.DB, which each
# analyzes with its own top and DUT.
UVM_TOPOLOGY_LIST = $(foreach t,$(UVM_TOPOLOGIES),$(addprefix $(firstword $(subst :, ,$(t))):,$(subst $(comma), ,$(word 2,$(subst :, ,$(t))))))

.PHONY: uvm_snapshots
uvm_snapshots: gen
	+$(foreach t,$(UVM_TOPOLOGY_LIST),$(MAKE) UVM_TOP=$(word 1,$(subst :, ,$(t))) UVM_DUT=$(word 2,$(subst :, ,$(t))) all &&) true

help::
	@echo "  USE_UVM=1                        - build the UVM snapshot run_uvm_<UVM_TOP>_<UVM_DUT> (needs USE_VCS=1 or USE_XCELIUM=1)"
	@echo "  UVM_TOP / UVM_DUT / UVM_TEST     - UVM testbench top stem, model or rtl DUT, default +UVM_TESTNAME"
	@echo "  uvm_snapshots                    - build one UVM snapshot per top and DUT in UVM_TOPOLOGIES (<top>:<dut>[,<dut>]...)"
