# Questa flow: vlog compiles the RTL into one DUT library, sccom links the
# SystemC objects into the SystemC library beside a small sccom-compiled sc_main
# (common/systemc/questa/questa_sc_main.cpp), vopt elaborates one optimized
# design per DUT topology, and build/run_<topology> is a script that runs it
# with vsim, the test's arguments passed through as -sc_arg; the command line
# matches the other flows. The libraries and the ini file live in
# QUESTA_RUNDIR; every topology of a build shares the two libraries, so only
# vopt runs per topology. a2c-systemc.mk checks QUESTA_HOME.

VLIB  ?= $(QUESTA_HOME)/bin/vlib
VLOG  ?= $(QUESTA_HOME)/bin/vlog
SCCOM ?= $(QUESTA_HOME)/bin/sccom
VOPT  ?= $(QUESTA_HOME)/bin/vopt
VSIM  ?= $(QUESTA_HOME)/bin/vsim

# -64 everywhere: without it sccom selects the 32-bit GCC of the install.
# -mfcu compiles the vlog command line as one compilation unit, as Verilator
# and xrun do, so a2c.f's flops.sv macros (`DFF_INST) reach the RTL.
QUESTA_VLOG_OPTS ?= -64 -mfcu -sv -timescale 1ns/1ps
# DONT_USE_MTI_EXIT keeps exit() a function; the Clang objects define it too.
QUESTA_SCCOM_OPTS ?= -64 -DDONT_USE_MTI_EXIT
# sc_main is the top; -noscmainscopename keeps it out of the instance names.
# 10003 is the note that sc_main calls exit (questa_sc_main.cpp passes the
# test's exit code on that way). -enablescstdout shows what a2c prints while
# vopt elaborates, an elaboration failure's message included.
QUESTA_VOPT_OPTS ?= -64 -noscmainscopename -suppress 10003 -enablescstdout
# -batch writes no transcript file and returns sc_main's exit code; -nolog
# keeps it so for a site whose ini names a TranscriptFile, as concurrent runs
# share QUESTA_RUNDIR. -t 1ps matches the RTL's -timescale. -scasyncupdate
# enables async_request_update(), which Questa disables by default and a2c's
# asyncEvent (firmware threads, sockets) calls.
QUESTA_VSIM_OPTS ?= -64 -batch -nolog -t 1ps -noscmainscopename -suppress 10003 -scasyncupdate
# The Tcl the simulation runs. A project replaces it to wrap the run, e.g.
# QUESTA_VSIM_DO = do $(REPO_ROOT)/include/make/my.tcl, with a script that ends
# in run -all. onerror/onbreak: under -batch, an error that stops the run (a
# Fatal SystemC error, an HDL $fatal) would otherwise end vsim with code 0.
QUESTA_VSIM_DO ?= onerror {quit -code 1}; onbreak {quit -code 1}; run -all

# Library names, also their directories in QUESTA_RUNDIR.
QUESTA_DUT_LIB ?= a2c_dut
QUESTA_SC_LIB  ?= a2c_sc
# a2c's instance names join with '.', and Questa's SystemC names follow
# PathSeparator, so the flow reads its own ini; it takes everything else,
# library mappings included, from the install's.
QUESTA_INI = $(QUESTA_RUNDIR)/a2c_questa.ini
$(shell mkdir -p $(QUESTA_RUNDIR); t=$$(printf '%s\n' '[Library]' 'others = $$MODEL_TECH/../questa.ini' '[vsim]' 'PathSeparator = .'); \
	[ "$$(cat $(QUESTA_INI) 2>/dev/null)" = "$$t" ] || printf '%s\n' "$$t" > $(QUESTA_INI))

# Boost enters the shared-library link, so it must be a shared or PIC library
# (BOOST_LIBS, shared with the other flows in a2c-systemc.mk). sccom -link
# passes the -L/-l words to its linker as given.
QUESTA_LD_LIBS = $(BOOST_LIBS) -ldl -lrt -lpthread $(A2C_LAYER_LD_FLAGS) $(EXTRA_LD_FLAGS)

QUESTA_STAMP_DIR = $(BUILD_DIR)/questa
QUESTA_SC_MAIN = $(A2C_ROOT)/common/systemc/questa/questa_sc_main.cpp

# The HDL: the arguments of a2c-xrun.mk's DUT library. vlog compiles in
# command-line order, the HDL hooks and EXTRA_QUESTA_VLOG_OPTS after a2c.f.
QUESTA_INCDIRS = $(addprefix +incdir+,$(A2C_VL_WRAP_DIRS))
QUESTA_TOP_SV = $(sort $(foreach t,$(A2C_VL_TOPS),$(A2C_VL_SV_$(t))))
ifdef VL_DUT
QUESTA_VLOG_ARGS = $(strip $(QUESTA_VLOG_OPTS) -work $(QUESTA_DUT_LIB) -F $(A2C_ROOT)/common/systemVerilog/a2c.f \
	$(A2C_HDL_ARGS) $(EXTRA_QUESTA_VLOG_OPTS) \
	-F $(A2C_RTL_DOT_F) $(A2C_SV_FILES) $(QUESTA_INCDIRS) $(QUESTA_TOP_SV))
QUESTA_HDL_DEPS = $(wildcard $(A2C_SV_DEP_FILES) $(EXTRA_SV_GEN_FILES)) $(A2C_RTL_DOT_F) $(QUESTA_TOP_SV) $(A2C_HDL_DEPS)
QUESTA_VLOG_STAMP = $(QUESTA_STAMP_DIR)/vlog
QUESTA_VOPT_LIBS = -L $(QUESTA_DUT_LIB) -L $(QUESTA_SC_LIB)
# The foreign-module shells the registrars include are generated under .gen/vl.
$(A2C_VL_REGISTRAR_SRC:%.cpp=$(BUILD_DIR)/%.o): $(VL_BOUNDARY_STAMP)
else
QUESTA_VLOG_STAMP =
QUESTA_VOPT_LIBS = -L $(QUESTA_SC_LIB)
endif

# Each tool command's arguments are recorded at parse time, so a change reruns
# that step even when no named file's mtime moves. The records are stripped:
# an empty hook appended to in a sub-make adds blanks, which would otherwise
# rewrite a record on every build and rerun its step.
QUESTA_VLOG_OPTS_STAMP = $(QUESTA_STAMP_DIR)/vlog_opts
QUESTA_SCLINK_ARGS = $(strip $(QUESTA_SCCOM_OPTS) $(QUESTA_LD_LIBS))
QUESTA_SCLINK_OPTS_STAMP = $(QUESTA_STAMP_DIR)/sclink_opts
$(shell mkdir -p $(QUESTA_STAMP_DIR); \
	[ "$$(cat $(QUESTA_VLOG_OPTS_STAMP) 2>/dev/null)" = "$(QUESTA_VLOG_ARGS)" ] || printf '%s\n' "$(QUESTA_VLOG_ARGS)" > $(QUESTA_VLOG_OPTS_STAMP); \
	[ "$$(cat $(QUESTA_SCLINK_OPTS_STAMP) 2>/dev/null)" = "$(QUESTA_SCLINK_ARGS)" ] || printf '%s\n' "$(QUESTA_SCLINK_ARGS)" > $(QUESTA_SCLINK_OPTS_STAMP))

ifdef VL_DUT
$(QUESTA_VLOG_STAMP): $(QUESTA_HDL_DEPS) $(QUESTA_VLOG_OPTS_STAMP)
	cd $(QUESTA_RUNDIR) && rm -rf $(QUESTA_DUT_LIB) && $(VLIB) $(QUESTA_DUT_LIB) && $(VLOG) $(QUESTA_VLOG_ARGS)
	touch $@
endif

# sccom -link needs at least one object sccom compiled itself, which the
# sc_main stub is; the Clang objects then join it in the library's systemc.so.
# $(OBJ) names an object twice when its source is both in a source directory
# and on EXTRA_CPP_SRC; the native link takes $^, which lists it once, so this
# link does too, keeping the first occurrence.
questa_uniq = $(if $(1),$(firstword $(1)) $(call questa_uniq,$(filter-out $(firstword $(1)),$(1))))
QUESTA_LINK_OBJ := $(call questa_uniq,$(OBJ))
QUESTA_SCLINK_STAMP = $(QUESTA_STAMP_DIR)/sclink
$(QUESTA_SCLINK_STAMP): $(OBJ) $(QUESTA_SC_MAIN) $(QUESTA_SCLINK_OPTS_STAMP)
	cd $(QUESTA_RUNDIR) && rm -rf $(QUESTA_SC_LIB) && $(VLIB) $(QUESTA_SC_LIB) && \
	$(SCCOM) $(QUESTA_SCCOM_OPTS) -work $(QUESTA_SC_LIB) $(QUESTA_SC_MAIN) && \
	$(SCCOM) $(QUESTA_SCCOM_OPTS) -work $(QUESTA_SC_LIB) -link $(QUESTA_LINK_OBJ) $(QUESTA_LD_LIBS)
	touch $@

# One optimized design per DUT topology, in its own library so the vopt runs of
# a regression build write to separate directories. vopt runs sc_main to
# elaborate the topology (main.cpp returns at the first sc_start), so it needs
# the testbench command line the design is later run with. Dots in the
# topology name would read as library.unit, so the library and the design unit
# spell them __.
QUESTA_SNAPSHOT = opt_$(subst .,__,$(DUT_TOPOLOGY))
QUESTA_OPT_LIB = a2c_opt_$(subst .,__,$(DUT_TOPOLOGY))
QUESTA_SNAP_STAMP_DIR = $(QUESTA_STAMP_DIR)/$(QUESTA_OPT_LIB)
QUESTA_VOPT_ARGS = $(strip $(QUESTA_VOPT_OPTS) $(EXTRA_QUESTA_VOPT_OPTS) $(QUESTA_VOPT_LIBS) $(QUESTA_SC_LIB).sc_main \
	$(addprefix -sc_arg ,$(DUT_ELAB_ARGS)))
QUESTA_VOPT_OPTS_STAMP = $(QUESTA_SNAP_STAMP_DIR)/opts
$(shell mkdir -p $(QUESTA_SNAP_STAMP_DIR); [ "$$(cat $(QUESTA_VOPT_OPTS_STAMP) 2>/dev/null)" = "$(QUESTA_VOPT_ARGS)" ] || printf '%s\n' "$(QUESTA_VOPT_ARGS)" > $(QUESTA_VOPT_OPTS_STAMP))

QUESTA_STAMP = $(QUESTA_SNAP_STAMP_DIR)/snapshot
$(QUESTA_STAMP): $(QUESTA_SCLINK_STAMP) $(QUESTA_VLOG_STAMP) $(QUESTA_VOPT_OPTS_STAMP)
	cd $(QUESTA_RUNDIR) && rm -rf $(QUESTA_OPT_LIB) && $(VLIB) $(QUESTA_OPT_LIB) && \
	$(VOPT) -ini $(QUESTA_INI) -work $(QUESTA_OPT_LIB) $(QUESTA_VOPT_ARGS) -o $(QUESTA_SNAPSHOT) -l vopt_$(DUT_TOPOLOGY).log
	touch $@

# vsim resolves the HDL units SystemC instantiates by name again, so it searches
# the libraries vopt did. The script carries the licence setting the build ran
# with, so a test launched outside this make environment finds the same
# servers. Its per-simulation options and licence setting are recorded so a
# change rewrites the script.
QUESTA_RUN_ARGS = $(QUESTA_VSIM_OPTS) $(EXTRA_QUESTA_VSIM_OPTS)
QUESTA_R_OPTS_STAMP = $(QUESTA_SNAP_STAMP_DIR)/r_opts
QUESTA_R_OPTS = $(strip $(QUESTA_RUN_ARGS) $(QUESTA_VSIM_DO) $(SALT_LICENSE_SERVER))
$(shell [ "$$(cat $(QUESTA_R_OPTS_STAMP) 2>/dev/null)" = "$(QUESTA_R_OPTS)" ] || printf '%s\n' "$(QUESTA_R_OPTS)" > $(QUESTA_R_OPTS_STAMP))

# vsim exits 0 after an HDL $error or a failed assertion, even under the
# onerror handler, so the script passes vsim's output through and fails the run
# on a "# ** Error", "# ** Fatal" or "# ** Failure" line: vsim's own non-zero
# exit code wins, else 1.
QUESTA_LOG_CHECK = awk "/^a2c_vsim_rc=/ { rc = substr(\$$0, 13); next } { print; fflush() } \
	/^\# \\*\\* (Error|Fatal|Failure)/ { e++ } \
	END { if (rc != 0) exit rc; if (e) { print \"a2c: vsim reported \" e \" error line(s)\" > \"/dev/stderr\"; exit 1 } }"

$(BIN_DIR)/$(BIN): $(QUESTA_STAMP) $(QUESTA_R_OPTS_STAMP)
	mkdir -p $(@D)
	printf '%s\n' '#!/bin/sh' \
		$(if $(SALT_LICENSE_SERVER),'export SALT_LICENSE_SERVER="$(SALT_LICENSE_SERVER)"') \
		'for a; do set -- "$$@" -sc_arg "$$a"; shift; done' \
		'cd $(QUESTA_RUNDIR) || exit 1' \
		'{ $(VSIM) -ini $(QUESTA_INI) $(QUESTA_RUN_ARGS) -lib $(QUESTA_OPT_LIB) $(QUESTA_VOPT_LIBS) $(QUESTA_SNAPSHOT) "$$@" -do "$(QUESTA_VSIM_DO)" 2>&1; echo "a2c_vsim_rc=$$?"; } | $(QUESTA_LOG_CHECK)' > $@
	chmod +x $@

help::
	@echo "  QUESTA_HOME                      - Questa release directory, holding bin/vsim (required with USE_QUESTA=1)"
	@echo "  questa_snapshots                 - build run_model and one optimized design per DUT_TOPOLOGIES entry"
	@echo "                                     (<inst>:<cfg>[,<cfg>]... with cfg = verif|model[:tandem]; normally set from the regression file build command)"

# Regression snapshots: run_model, whose build also compiles the HDL and links
# the shared SystemC library once, then one vopt per DUT_TOPOLOGY_LIST entry,
# each in its own library, so they run in parallel. dutRun.py maps a test's
# arguments to the snapshot with the same naming.
ifeq ($(VL_DUT),)
ifneq ($(filter questa_snapshots,$(MAKECMDGOALS)),)
$(error questa_snapshots builds the DUT snapshots; VL_DUT= selects the model-only snapshot)
endif
endif
QUESTA_SNAPSHOTS = $(addprefix questa_snapshot+,$(subst :,+,$(DUT_TOPOLOGY_LIST)))

.PHONY: questa_snapshots
questa_snapshots: gen
	+$(MAKE) VL_INST= $(BIN_DIR)/run_model
	+$(MAKE) $(QUESTA_SNAPSHOTS)

questa_snapshot+%:
	+$(call dut_topology_make,$(subst +,:,$*)) all
