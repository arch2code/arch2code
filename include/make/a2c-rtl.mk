#------------------------------------------------------------------------
# Check mandatory variables are set when including this makefile
#------------------------------------------------------------------------

ifndef REPO_ROOT
$(error REPO_ROOT is not set - please set to the root of your repository)
endif
ifndef PROJECTNAME
$(error PROJECTNAME is not set - please set to the name of your project)
endif
ifndef HDL_TOP_MODULE
$(error HDL_TOP_MODULE is not set - please set to the name of the top HDL module of your project)
endif

#------------------------------------------------------------------------
# RTL build global variables
#------------------------------------------------------------------------

VERILATOR_OPTS = --no-timing --lint-only

VERILATOR_OPTS += $(VERILATOR_USER_OPTS)

TOP_HDL_SV_WRAPPER_NAME = $(HDL_TOP_MODULE)_hdl_sv_wrapper
# Top wrapper source comes from the manifest's per-top record (keyed by the
# wrapper design-unit name), which is layout-correct: functional
# ($root/verif/vl_wrap) and hierarchical (node-scoped <node>/verif) alike.
TOP_HDL_SV_WRAPPER_FILE = $(A2C_VL_SV_$(TOP_HDL_SV_WRAPPER_NAME))

RTL_DOT_F_FILE = $(A2C_RTL_DOT_F)

RTL_SRC_FILES += $(TOP_HDL_SV_WRAPPER_FILE)


#------------------------------------------------------------------------
# Systemc build phony targets
#------------------------------------------------------------------------

.PHONY : all lint
.DEFAULT_GOAL := all lint

all : lint

lint: gen $(RTL_DOT_F_FILE)
	verilator  $(VERILATOR_OPTS) --top-module $(TOP_HDL_SV_WRAPPER_NAME) -F $(A2C_ROOT)/common/systemVerilog/a2c.f -f $(RTL_DOT_F_FILE) $(A2C_SV_FILES) $(RTL_SRC_FILES)

help::
	@echo "  all     	- Run all lint checks"
	@echo "  lint    	- Run lint checks on the HDL files"
	@echo "  help    	- Show this help message"
