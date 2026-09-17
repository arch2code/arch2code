# Xcelium flow: one xrun invocation compiles the RTL, links the SystemC objects
# into its shared library, elaborates and writes one snapshot per DUT topology in
# XRUN_RUNDIR. Xcelium fixes the SystemC topology at elaboration, so the snapshot
# is elaborated with the topology's testbench arguments and build/run_<topology>
# is a script that re-simulates it with the test's arguments passed through as
# +systemc_args+; the command line matches the other flows.

# xrun links the SystemC objects with the GCC release named by -gcc_vers, which
# must match the libstdc++ they were compiled against; the install-specific
# value comes from the site configuration.
ifndef XRUN_GCC_VERS
$(error XRUN_GCC_VERS is not set - set it to the Xcelium -gcc_vers release matching the compiler's libstdc++ to build with USE_XCELIUM)
endif

XRUN ?= xrun
XRUN_OPTS ?= -64bit -sv -sysc -sc_main -timescale 1ns/1ps -warn_multiple_driver
XRUN_OPTS += -gcc_vers $(XRUN_GCC_VERS) $(XRUN_USER_OPTS)
# Per-simulation options; -nolog so concurrent runs do not fight over xrun.log.
XRUN_R_OPTS ?= -64bit -nolog

# Boost enters the shared-library link, so it must be a shared or PIC library.
# Boost.System is header-only and the header-only stacktrace needs only -ldl.
XRUN_BOOST_LIBS ?= -lboost_program_options
# xrun forwards each -Wld,<arg> to the linker as one argument, so a
# comma-carrying -Wl,-rpath,<dir> cannot be expressed; runtime library paths
# come from LD_LIBRARY_PATH.
comma := ,
XRUN_LD_LIBS = $(addprefix -Wld$(comma),$(XRUN_BOOST_LIBS) -ldl -lrt -lpthread $(EXTRA_LD_FLAGS))

XRUN_INCDIRS = $(addprefix +incdir+,$(A2C_VL_WRAP_DIRS))
XRUN_TOP_SV = $(sort $(foreach t,$(A2C_VL_TOPS),$(A2C_VL_SV_$(t))))
# The HDL is compiled into its own library. xmelab still elaborates the wrapper
# tops the topology does not instantiate as idle top-levels.
XRUN_DUT_LIB ?= a2c_dut
ifdef VL_DUT
XRUN_HDL = -makelib $(XRUN_DUT_LIB) -F $(A2C_ROOT)/common/systemVerilog/a2c.f -F $(A2C_RTL_DOT_F) $(A2C_SV_FILES) \
	$(XRUN_INCDIRS) $(XRUN_TOP_SV) -endlib
XRUN_HDL_DEPS = $(wildcard $(A2C_SV_DEP_FILES) $(EXTRA_SV_GEN_FILES)) $(A2C_RTL_DOT_F) $(XRUN_TOP_SV)
# The foreign-module shells the registrars include are generated under .gen/vl.
$(A2C_VL_REGISTRAR_SRC:%.cpp=$(BUILD_DIR)/%.o): $(VL_BOUNDARY_STAMP)
endif

# One snapshot directory per DUT topology, so the topologies coexist in XRUN_RUNDIR.
XRUN_SNAPSHOT_DIR = xcelium_$(DUT_TOPOLOGY).d
XRUN_STAMP_DIR = $(BUILD_DIR)/xrun/$(XRUN_SNAPSHOT_DIR)

XRUN_STAMP = $(XRUN_STAMP_DIR)/snapshot
# Options, elaboration arguments, link libraries, and the HDL compile command
# (include dirs and source lists) shape the snapshot; record them so a change
# rebuilds it even when no named file's mtime moves.
XRUN_SNAPSHOT_OPTS = $(XRUN_OPTS) $(DUT_ELAB_ARGS) $(XRUN_LD_LIBS) $(XRUN_HDL)
XRUN_OPTS_STAMP = $(XRUN_STAMP_DIR)/opts
$(shell mkdir -p $(XRUN_STAMP_DIR); [ "$$(cat $(XRUN_OPTS_STAMP) 2>/dev/null)" = "$(XRUN_SNAPSHOT_OPTS)" ] || printf '%s\n' "$(XRUN_SNAPSHOT_OPTS)" > $(XRUN_OPTS_STAMP))

$(XRUN_STAMP): $(OBJ) $(XRUN_HDL_DEPS) $(XRUN_OPTS_STAMP)
	cd $(XRUN_RUNDIR) && $(XRUN) $(XRUN_OPTS) -clean -xmlibdirname $(XRUN_SNAPSHOT_DIR) $(XRUN_HDL) $(OBJ) $(XRUN_LD_LIBS) $(addprefix +systemc_args+,$(DUT_ELAB_ARGS)) -l xrun_$(XRUN_SNAPSHOT_DIR:%.d=%).log
	touch $@

# The script carries the licence setting the build ran with, so a test launched
# outside this make environment finds the same servers. Its per-simulation
# options and licence list are recorded so a change rewrites the script.
XRUN_R_OPTS_STAMP = $(XRUN_STAMP_DIR)/r_opts
$(shell [ "$$(cat $(XRUN_R_OPTS_STAMP) 2>/dev/null)" = "$(XRUN_R_OPTS) $(LM_LICENSE_FILE)" ] || printf '%s\n' "$(XRUN_R_OPTS) $(LM_LICENSE_FILE)" > $(XRUN_R_OPTS_STAMP))

$(BIN_DIR)/$(BIN): $(XRUN_STAMP) $(XRUN_R_OPTS_STAMP)
	mkdir -p $(@D)
	printf '%s\n' '#!/bin/sh' \
		$(if $(LM_LICENSE_FILE),'export LM_LICENSE_FILE="$(LM_LICENSE_FILE)"') \
		'args=""; for a in "$$@"; do args="$$args +systemc_args+$$a"; done' \
		'cd $(XRUN_RUNDIR) && exec $(XRUN) -R -xmlibdirname $(XRUN_SNAPSHOT_DIR) $(XRUN_R_OPTS) $$args' > $@
	chmod +x $@

help::
	@echo "  XRUN_USER_OPTS / XRUN_R_OPTS     - extra options for the Xcelium snapshot build / each simulation (USE_XCELIUM=1)"
	@echo "  XCELIUM_TOOLS / XRUN_GCC_VERS    - Xcelium install tools directory and -gcc_vers release (required with USE_XCELIUM=1)"
	@echo "  xrun_snapshots                   - build run_model and one snapshot per DUT_TOPOLOGIES entry (<inst>:verif[:tandem])"

# Regression snapshots: run_model plus one per DUT_TOPOLOGIES entry. Each
# snapshot has its own library directory and log, so they elaborate in parallel
# once the model build has compiled the shared objects. dutRun.py maps a test's
# arguments to the snapshot with the same naming.
ifeq ($(VL_DUT),)
ifneq ($(filter xrun_snapshots,$(MAKECMDGOALS)),)
$(error xrun_snapshots builds the DUT snapshots; VL_DUT= selects the model-only snapshot)
endif
endif
XRUN_SNAPSHOTS = $(addprefix xrun_snapshot+,$(subst :,+,$(DUT_TOPOLOGIES)))

.PHONY: xrun_snapshots
xrun_snapshots: gen
	+$(MAKE) VL_INST= $(BIN_DIR)/run_model
	+$(MAKE) $(XRUN_SNAPSHOTS)

xrun_snapshot+%:
	+$(call dut_topology_make,$(subst +,:,$*)) all
