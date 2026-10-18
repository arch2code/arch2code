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
VCS_ELAB_OPTS ?= -sysc=234
# Verdi/FSDB debug costs simulation time, so it is opt-in: -kdb -debug_access
# at link, and VCS_DEBUG defined for the wrappers' $fsdbDumpvars call.
ifdef VCS_DEBUG
VCS_ELAB_OPTS += -kdb -debug_access
VLOGAN_OPTS += +define+VCS_DEBUG
endif
# UVM 1.2 from VCS_HOME/etc/uvm-1.2: vlogan needs it to analyze the packages
# that import uvm_pkg, and vcs to link the UVM DPI library.
ifdef USE_UVM
VLOGAN_OPTS += -ntb_opts uvm-1.2
VCS_OPTS += -ntb_opts uvm-1.2
endif

# Design units a2c.f offers through -y search dirs. vcs does not consult those
# at elaboration in the vlogan flow, so they are analyzed explicitly with the
# design. a2c.f already names flops.sv and asserts.svh.
VCS_LIB_SV_FILES ?= $(wildcard $(A2C_ROOT)/interfaces/*/*_if.sv) \
	$(wildcard $(A2C_ROOT)/interfaces/*/*_xcheck.sv) \
	$(filter-out %/flops.sv,$(wildcard $(A2C_ROOT)/common/systemVerilog/*.sv))
VCS_LIB_SV_FILES += $(A2C_LAYER_VCS_LIB_SV_FILES) $(EXTRA_VCS_LIB_SV_FILES)

VCS_SV_DEPS = $(wildcard $(A2C_SV_DEP_FILES) $(EXTRA_SV_GEN_FILES)) $(A2C_RTL_DOT_F)
# common/systemVerilog holds hdlBoundary.svh, which every wrapper with port assigns includes.
VCS_INCDIRS = $(addprefix +incdir+,$(A2C_ROOT)/common/systemVerilog $(A2C_VL_WRAP_DIRS))

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

# The X/Z checkers in VCS_LIB_SV_FILES include a2c_xcheck.svh.
$(VCS_RTL_STAMP): $(VCS_SV_DEPS) $(VCS_LIB_SV_FILES) $(A2C_ROOT)/common/systemVerilog/a2c_xcheck.svh \
	$(A2C_HDL_DEPS) $(VCS_VLOGAN_STAMP)
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

# A UVM snapshot's simv sits beside the run script that carries its name.
VCS_SIMV = $(BIN_DIR)/$(BIN)$(if $(USE_UVM),.simv)

# VCS reuses the per-binary topology (csrc/sysc/<binary>/sysc_skeleton.v) it
# discovered on an earlier link, so those caches are dropped before linking; a
# fresh discovery run costs a few seconds.
# A failed link leaves csrc/ and AN.DB in a state vcs rejects next time (NTMES),
# so both analysis steps are redone after a failure.
# VCS's own internal make must not inherit this make's jobserver fds, so they
# are cleared from its environment before invoking vcs.
$(VCS_SIMV): $(VCS_LINK_DEPS) $(VCS_ELAB_STAMP)
	mkdir -p $(@D)
	cd $(VCS_RUNDIR) || exit 1; for skel in csrc/sysc/*/sysc_skeleton.v; do [ -e "$$skel" ] && $(RM) -r "$${skel%/*}"; done; \
		MAKEFLAGS= MFLAGS= $(VCS) $(VCS_OPTS) $(VCS_ELAB_OPTS) $(addprefix -syscelab ,$(DUT_ELAB_ARGS)) $(EXTRA_VCS_OPTS) -l vcs.log $(VCS_LD_FLAGS) $(OBJ) sc_main -o $@ \
		|| { $(RM) -rf csrc AN.DB $(VCS_RTL_STAMP) $(VCS_SC_MODEL_STAMP); exit 1; }

ifdef USE_UVM
# In the vlogan flow -ntb_opts uvm-1.2 only adds the UVM include dirs, so
# uvm_pkg itself is analyzed first, by a vlogan run with no source files. Its
# stamp sits in AN.DB, which a failed link deletes. The options file
# re-analyzes it when the vlogan options or the VCS install change.
VCS_UVM_PKG_STAMP = $(VCS_RUNDIR)/AN.DB/uvm_pkg.a2c_stamp
VCS_UVM_PKG_OPTS = $(VCS_STAMP_DIR)/uvm_pkg_opts
VCS_UVM_PKG_OPTS_TEXT = $(VLOGAN_OPTS) $(EXTRA_VLOGAN_OPTS) VCS_HOME=$(VCS_HOME)
$(shell [ "$$(cat $(VCS_UVM_PKG_OPTS) 2>/dev/null)" = "$(VCS_UVM_PKG_OPTS_TEXT)" ] || printf '%s\n' "$(VCS_UVM_PKG_OPTS_TEXT)" > $(VCS_UVM_PKG_OPTS))
$(VCS_RTL_STAMP): $(VCS_UVM_PKG_STAMP)
$(VCS_UVM_PKG_STAMP): $(VCS_UVM_PKG_OPTS)
	cd $(VCS_RUNDIR) && $(VLOGAN) $(VLOGAN_OPTS) $(EXTRA_VLOGAN_OPTS) -l vlogan_uvm_pkg.log
	touch $@

# One shell per UVM top, because the registrar includes them all, made after
# the wrapper tops' in the same AN.DB. Another top's variant package is
# analyzed before its testbench module, and the selected top comes last. The
# HDL defines are repeated because vlogan re-analyzes the source it is given,
# and A2C_UVM_RTL_DUT changes the testbench module's body.
VCS_UVM_SHELL_STAMP = $(VCS_STAMP_DIR)/uvm_sc_model.vlogan
VCS_UVM_PORTMAPS = $(foreach t,$(A2C_UVM_TOPS),$(A2C_UVM_PORTMAP_$(t)))
VCS_UVM_OTHER_TOPS = $(filter-out $(UVM_TB_TOP),$(A2C_UVM_TOPS))
VCS_UVM_VLOGAN = $(VLOGAN) $(VLOGAN_OPTS) $(EXTRA_VLOGAN_OPTS) $(addprefix +define+,$(EXTRA_HDL_DEFINES) $(A2C_UVM_HDL_DEFINES))
$(VCS_UVM_SHELL_STAMP): $(VCS_SC_MODEL_STAMP) $(VCS_UVM_PORTMAPS) \
	$(foreach t,$(A2C_UVM_TOPS),$(A2C_UVM_PKG_SV_$(t)) $(A2C_UVM_TB_SV_$(t)))
	cd $(VCS_RUNDIR) && $(foreach t,$(VCS_UVM_OTHER_TOPS),$(VCS_UVM_VLOGAN) $(A2C_UVM_PKG_SV_$(t)) -l vlogan_$(t)_pkg.log &&) \
		$(foreach t,$(VCS_UVM_OTHER_TOPS) $(UVM_TB_TOP),$(VCS_UVM_VLOGAN) -sc_model $(t) -sc_portmap $(A2C_UVM_PORTMAP_$(t)) $(VCS_INCDIRS) $(A2C_UVM_TB_SV_$(t)) -l vlogan_$(t).log &&) true
	touch $@
$(VCS_UVM_PORTMAPS): $(VL_BOUNDARY_STAMP) ;

$(A2C_UVM_REGISTRAR_SRC:%.cpp=$(BUILD_DIR)/%.o) $(VCS_SIMV): $(VCS_UVM_SHELL_STAMP)
$(VCS_SIMV): $(OBJ)

# The run script hands the simv its arguments with the seed made decimal for
# both sides: --seed N for sc_main and +ntb_random_seed=N for the SV solver,
# which reads only decimal. UVM_TEST gives the +UVM_TESTNAME of a run that
# names none. The default test is recorded so a change rewrites the script.
VCS_RUN_SCRIPT_STAMP = $(VCS_STAMP_DIR)/$(BIN).run_script
$(shell [ -e $(VCS_RUN_SCRIPT_STAMP) ] && [ "$$(cat $(VCS_RUN_SCRIPT_STAMP))" = "$(UVM_TEST)" ] || printf '%s\n' "$(UVM_TEST)" > $(VCS_RUN_SCRIPT_STAMP))
$(BIN_DIR)/$(BIN): $(VCS_SIMV) $(VCS_RUN_SCRIPT_STAMP)
	printf '%s\n' '#!/bin/bash' 'set -e' \
		'dec() {' \
		'    case "$$1" in' \
		'        0[xX]*) v=$$((16#$${1#??})) ;;' \
		'        *) v=$$((10#$$1)) ;;' \
		'    esac' \
		'    [ "$$v" -le 4294967295 ] || { echo "$$0: --seed $$1 does not fit in 32 bits" >&2; exit 2; }' \
		'    echo "$$v"' \
		'}' \
		's=; t=' \
		'for a; do' \
		'    shift' \
		'    if [ -n "$$s" ]; then s=; v=$$(dec "$$a"); set -- "$$@" "$$v" "+ntb_random_seed=$$v"; continue; fi' \
		'    case "$$a" in' \
		'        --seed) s=1; set -- "$$@" "$$a" ;;' \
		'        --seed=*) v=$$(dec "$${a#--seed=}"); set -- "$$@" "--seed=$$v" "+ntb_random_seed=$$v" ;;' \
		'        +UVM_TESTNAME=*) t=1; set -- "$$@" "$$a" ;;' \
		'        *) set -- "$$@" "$$a" ;;' \
		'    esac' \
		'done' \
		$(if $(UVM_TEST),'[ -n "$$t" ] || set -- "$$@" +UVM_TESTNAME=$(UVM_TEST)') \
		'exec $(VCS_SIMV) "$$@"' > $@
	chmod +x $@
endif

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
