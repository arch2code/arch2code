# VCS SystemVerilog-in-SystemC flow: vlogan analyzes the RTL, generates one
# SystemC shell per verification-wrapper top (A2C_VL_TOPS, pin widths/types from
# A2C_VL_PORTMAP_<top>), and vcs links the SystemC objects with the elaborated
# HDL. VCS first runs the SystemC part alone to discover the instantiated HDL
# models, so the simv arguments that shape the topology are passed with
# -syscelab and must be repeated at run time; one compile serves every topology,
# only the link is per topology.

ifndef VCS_HOME
$(error VCS_HOME is not set - load the VCS environment before building with USE_VCS)
endif

VCS ?= vcs
VLOGAN ?= vlogan
VCS_OPTS ?= +vcs+lic+wait -full64 -timescale=1ns/1ps
VLOGAN_OPTS ?= +vcs+lic+wait -full64 -sverilog -timescale=1ns/1ps
VCS_ELAB_OPTS ?= -sysc=234 -ignore initial_driver_checks
# Verdi/FSDB debug costs simulation time, so it is opt-in: -kdb -debug_access
# at link, and VCS_DEBUG defined for the wrappers' $fsdbDumpvars call.
ifdef VCS_DEBUG
VCS_ELAB_OPTS += -kdb -debug_access
VLOGAN_OPTS += +define+VCS_DEBUG
endif

# Design units a2c.f offers through -y search dirs. vcs does not consult those
# at elaboration in the vlogan flow, so they are analyzed explicitly with the
# design. a2c.f already names flops.sv and asserts.svh.
VCS_LIB_SV_FILES ?= $(wildcard $(A2C_ROOT)/interfaces/*/*_if.sv) \
	$(filter-out %/flops.sv,$(wildcard $(A2C_ROOT)/common/systemVerilog/*.sv))
VCS_LIB_SV_FILES += $(A2C_LAYER_VCS_LIB_SV_FILES) $(EXTRA_VCS_LIB_SV_FILES)

VCS_SV_DEPS = $(wildcard $(A2C_SV_DEP_FILES) $(EXTRA_SV_GEN_FILES)) $(A2C_RTL_DOT_F)
VCS_INCDIRS = $(addprefix +incdir+,$(A2C_VL_WRAP_DIRS))

VCS_STAMP_DIR = $(BUILD_DIR)/vcs
VCS_RTL_STAMP = $(VCS_STAMP_DIR)/rtl.vlogan
VCS_SC_MODEL_STAMP = $(VCS_STAMP_DIR)/sc_model.vlogan
VCS_PORTMAPS = $(foreach t,$(A2C_VL_TOPS),$(A2C_VL_PORTMAP_$(t)))
VCS_TOP_SV = $(foreach t,$(A2C_VL_TOPS),$(A2C_VL_SV_$(t)))

# The RTL analysis arguments: builder options, the project's vlogan hook, then
# the sources, with the HDL hooks between a2c.f and the project's rtl.f. They
# are part of the analysis; record them so a change re-analyzes even when no
# named file's mtime moves (for instance a source list gaining a pre-existing
# file). They hold every -sc_model option and include dir too, so one stamp
# covers both vlogan stages.
VCS_ANALYSIS_OPTS = $(VLOGAN_OPTS) $(EXTRA_VLOGAN_OPTS) -F $(A2C_ROOT)/common/systemVerilog/a2c.f $(A2C_HDL_ARGS) \
	-F $(A2C_RTL_DOT_F) $(A2C_SV_FILES) $(VCS_LIB_SV_FILES) $(VCS_INCDIRS)
VCS_VLOGAN_STAMP = $(VCS_STAMP_DIR)/vlogan_opts
$(shell mkdir -p $(VCS_STAMP_DIR); [ "$$(cat $(VCS_VLOGAN_STAMP) 2>/dev/null)" = "$(VCS_ANALYSIS_OPTS)" ] || printf '%s\n' "$(VCS_ANALYSIS_OPTS)" > $(VCS_VLOGAN_STAMP))

$(VCS_RTL_STAMP): $(VCS_SV_DEPS) $(VCS_LIB_SV_FILES) $(A2C_HDL_DEPS) $(VCS_VLOGAN_STAMP)
	mkdir -p $(@D)
	cd $(VCS_RUNDIR) && $(VLOGAN) $(VCS_ANALYSIS_OPTS) -l vlogan_rtl.log
	touch $@

# One shell per top. vlogan -sc_model takes a single source file and the runs
# share AN.DB, so they are sequenced in one recipe.
$(VCS_SC_MODEL_STAMP): $(VCS_RTL_STAMP) $(VCS_TOP_SV) $(VCS_PORTMAPS) $(VCS_VLOGAN_STAMP)
	cd $(VCS_RUNDIR) && $(foreach t,$(A2C_VL_TOPS),$(VLOGAN) $(VLOGAN_OPTS) $(EXTRA_VLOGAN_OPTS) -sc_model $(t) -sc_portmap $(A2C_VL_PORTMAP_$(t)) $(VCS_INCDIRS) $(A2C_VL_SV_$(t)) -l vlogan_$(t).log &&) true
	touch $@

# The port maps are outputs of the boundary generation step (a2c-common.mk).
$(VCS_PORTMAPS): $(VL_BOUNDARY_STAMP) ;

ifdef VL_DUT
$(A2C_VL_REGISTRAR_SRC:%.cpp=$(BUILD_DIR)/%.o): $(VCS_SC_MODEL_STAMP)
VCS_LINK_DEPS = $(VCS_SC_MODEL_STAMP)
endif

# vcs ignores -pthread (Warning-[UNKWN_OPTVSIM]) and links libpthread itself.
VCS_LD_FLAGS = $(filter-out -pthread,$(LD_FLAGS))

# The link command's options, elaboration arguments, and linker flags are part
# of the snapshot: record them per binary so a change relinks without
# recompiling and the topologies do not overwrite each other's record.
VCS_LINK_OPTS = $(VCS_OPTS) $(VCS_ELAB_OPTS) $(EXTRA_VCS_OPTS) $(VCS_LD_FLAGS) $(DUT_ELAB_ARGS)
VCS_ELAB_STAMP = $(VCS_STAMP_DIR)/$(BIN).elab_args
$(shell mkdir -p $(VCS_STAMP_DIR); [ "$$(cat $(VCS_ELAB_STAMP) 2>/dev/null)" = "$(VCS_LINK_OPTS)" ] || printf '%s\n' "$(VCS_LINK_OPTS)" > $(VCS_ELAB_STAMP))

# VCS reuses the per-binary topology (csrc/sysc/<binary>/sysc_skeleton.v) it
# discovered on an earlier link, so those caches are dropped before linking; a
# fresh discovery run costs a few seconds.
# A failed link leaves csrc/ and AN.DB in a state vcs rejects next time (NTMES),
# so both analysis steps are redone after a failure.
# VCS's own internal make must not inherit this make's jobserver fds, so they
# are cleared from its environment before invoking vcs.
$(BIN_DIR)/$(BIN): $(VCS_LINK_DEPS) $(VCS_ELAB_STAMP)
	mkdir -p $(@D)
	cd $(VCS_RUNDIR) || exit 1; for skel in csrc/sysc/*/sysc_skeleton.v; do [ -e "$$skel" ] && $(RM) -r "$${skel%/*}"; done; \
		MAKEFLAGS= MFLAGS= $(VCS) $(VCS_OPTS) $(VCS_ELAB_OPTS) $(addprefix -syscelab ,$(DUT_ELAB_ARGS)) $(EXTRA_VCS_OPTS) -l vcs.log $(VCS_LD_FLAGS) $(OBJ) sc_main -o $@ \
		|| { $(RM) -rf csrc AN.DB $(VCS_RTL_STAMP) $(VCS_SC_MODEL_STAMP); exit 1; }

help::
	@echo "  VCS_DEBUG=1                      - link with -kdb -debug_access and enable \$$fsdbDumpvars (+fsdbTrace)"
	@echo "  VL_INST / VL_TYPE / VL_TANDEM=1  - DUT topology of the VCS snapshot build/run_<inst>_<type>[_tandem];"
	@echo "                                     repeat the same --vlInst/--vlType/--vlTandem when running it"

# Regression snapshots: run_model plus one link per DUT_TOPOLOGY_LIST entry
# (a2c-systemc.mk). The links share AN.DB and csrc, so they run in sequence;
# the objects are compiled once. dutRun.py maps a test's arguments to the
# snapshot with the same naming.
ifeq ($(VL_DUT),)
ifneq ($(filter vcs_snapshots,$(MAKECMDGOALS)),)
$(error vcs_snapshots links the DUT snapshots; VL_DUT= selects the model-only binary)
endif
endif

.PHONY: vcs_snapshots
vcs_snapshots: gen
	+$(MAKE) VL_INST= $(BIN_DIR)/run_model
	+$(foreach t,$(DUT_TOPOLOGY_LIST),$(call dut_topology_make,$(t)) all &&) true

help::
	@echo "  vcs_snapshots                    - link build/run_model and one snapshot per DUT_TOPOLOGIES entry"
	@echo "                                     (<inst>:<cfg>[,<cfg>]... with cfg = verif|model[:tandem]; normally set from the regression file build command)"
