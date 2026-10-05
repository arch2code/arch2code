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

# The lint top is the DUT-top wrapper the manifest resolved for HDL_TOP_MODULE:
# an exact per-block lookup (A2C_VL_TOP_<block>) into the manifest, carrying that
# top block's instance variant. Unlike a prefix match against A2C_VL_TOPS it is
# exactly one entry -- unambiguous when the top block declares several variants
# (debayer_default vs debayer_wide), a verilated sibling shares the name prefix
# (debayer_regs_...), or several verilated top-level children exist (pySocket).
# It resolves the parameterized default variant (debayer ->
# debayer_default_hdl_sv_wrapper) and the non-parameterized form (mixed ->
# mixed_hdl_sv_wrapper) alike. An explicit command-line override still wins (?=).
TOP_HDL_SV_WRAPPER_NAME ?= $(A2C_VL_TOP_$(HDL_TOP_MODULE))
# Top wrapper source comes from the manifest's per-top record (keyed by the
# wrapper design-unit name), which is layout-correct: functional
# ($root/verif/vl_wrap) and hierarchical (node-scoped <node>/verif) alike.
TOP_HDL_SV_WRAPPER_FILE = $(A2C_VL_SV_$(TOP_HDL_SV_WRAPPER_NAME))

RTL_DOT_F_FILE = $(A2C_RTL_DOT_F)
SYNTH_DOT_F_FILE = $(GEN_BUILD_DIR)/synth.f

RTL_SRC_FILES += $(TOP_HDL_SV_WRAPPER_FILE)


#------------------------------------------------------------------------
# Systemc build phony targets
#------------------------------------------------------------------------

.PHONY : all lint synthf
.DEFAULT_GOAL := all lint

all : lint

# A top module with interface ports elaborates only inside its Verilator
# wrapper, so lint requires one.
lint: gen $(RTL_DOT_F_FILE)
	$(if $(TOP_HDL_SV_WRAPPER_NAME),,$(error HDL_TOP_MODULE '$(HDL_TOP_MODULE)' has no Verilator wrapper in the build manifest. \
	Lint needs the top instance's block or one of its direct children with hasVl: true \
	(available: $(or $(patsubst A2C_VL_TOP_%,%,$(filter A2C_VL_TOP_%,$(.VARIABLES))),none)), \
	or set TOP_HDL_SV_WRAPPER_NAME to the lint top))
	verilator  $(VERILATOR_OPTS) --top-module $(TOP_HDL_SV_WRAPPER_NAME) -F $(A2C_ROOT)/common/systemVerilog/a2c.f -f $(RTL_DOT_F_FILE) $(A2C_SV_FILES) $(addprefix +incdir+,$(A2C_VL_WRAP_DIRS)) $(RTL_SRC_FILES)

define SYNTH_NEWLINE


endef
SYNTH_FILES = $(strip $(A2C_SV_PACKAGE_FILES) $(A2C_SV_FILES))

# Packages in compile order, then the manifest RTL modules, one path per line.
# The Verilator wrapper and RTL_SRC_FILES additions are not listed. Make writes
# the file itself since the list can exceed a shell argument, and an empty list
# uses $(file >f) because $(file >f,) writes a newline.
synthf: gen
	$(if $(SYNTH_FILES),$(file >$(SYNTH_DOT_F_FILE),$(subst $() ,$(SYNTH_NEWLINE),$(SYNTH_FILES))),$(file >$(SYNTH_DOT_F_FILE)))
	@echo "Wrote $(SYNTH_DOT_F_FILE)"

help::
	@echo "  all     	- Run all lint checks"
	@echo "  lint    	- Run lint checks on the HDL files"
	@echo "  synthf  	- Write the synthesis file list (packages, then modules) to .gen/synth.f"
	@echo "  help    	- Show this help message"
