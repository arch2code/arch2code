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
TOP_HDL_SV_WRAPPER_FILE = $(REPO_ROOT)/verif/vl_wrap/$(TOP_HDL_SV_WRAPPER_NAME).sv

RTL_DOT_F_FILE = $(REPO_ROOT)/rtl/rtl.f

RTL_SRC_FILES += $(REPO_ROOT)/rtl/$(HDL_TOP_MODULE).sv $(TOP_HDL_SV_WRAPPER_FILE)


#------------------------------------------------------------------------
# Systemc build phony targets
#------------------------------------------------------------------------

.PHONY : all lint
.DEFAULT_GOAL := all lint

all : lint

lint: gen $(RTL_DOT_F_FILE)
	verilator  $(VERILATOR_OPTS) --top-module $(TOP_HDL_SV_WRAPPER_NAME) -F $(A2C_ROOT)/common/systemVerilog/a2c.f -f $(RTL_DOT_F_FILE) $(RTL_SRC_FILES)

help::
	@echo "  all     	- Run all lint checks"
	@echo "  lint    	- Run lint checks on the HDL files"
	@echo "  help    	- Show this help message"