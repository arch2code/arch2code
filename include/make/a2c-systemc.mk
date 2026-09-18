#------------------------------------------------------------------------
# Check mandatory variables are set when including this makefile
#------------------------------------------------------------------------

ifndef REPO_ROOT
$(error REPO_ROOT is not set - please set to the root of your repository)
endif
ifndef A2C_ROOT
$(error A2C_ROOT is not set - please set to the root of your A2C builder)
endif
ifndef PROJECTNAME
$(error PROJECTNAME is not set - please set to the name of your project)
endif
ifndef PROJECT_RUNDIR
$(error PROJECT_RUNDIR is not set - please set to the root of your project run directory)
endif
# SYSTEMC_INCLUDE/SYSTEMC_LIBDIR/BOOST_LIBS are the plain and VCS flows' own
# SystemC and Boost link inputs. Xcelium compiles against its own SystemC
# (XCELIUM_TOOLS, below) and links through XRUN_LD_LIBS instead of LD_FLAGS, so
# it never reads any of the three; only its own USE_XCELIUM checks apply.
ifndef USE_XCELIUM
ifndef SYSTEMC_INCLUDE
$(error SYSTEMC_INCLUDE is not set - please set to systemc-2.3.4 <install directory>/include)
endif
ifndef SYSTEMC_LIBDIR
$(error SYSTEMC_LIBDIR is not set - please set to systemc-2.3.4 <install directory>/lib)
endif
endif
ifndef BOOST_INCLUDE
$(error BOOST_INCLUDE is not set - please set to boost library <install directory>/include)
endif
# LD_BOOST is only needed by the BOOST_LIBS default below (the static site
# Boost's directory); a caller that sets BOOST_LIBS itself (linking a shared
# Boost) does not need it.
ifndef USE_XCELIUM
ifeq ($(origin BOOST_LIBS),undefined)
ifndef LD_BOOST
$(error LD_BOOST is not set - please set to boost library (.so) path)
endif
endif
endif

ifndef VERILATOR_ROOT
VERILATOR_ROOT=/usr/local/share/verilator
endif

#------------------------------------------------------------------------
# Systemc build global variables
#------------------------------------------------------------------------

# Language-standard flag passed to the compiler. Defaults to C_STD_VER, but is a
# separate knob so a toolchain whose -std spelling differs (e.g. Clang 16 uses
# `c++2b`, not `c++23`) can override the flag without flipping C_STD_VER, which
# also gates the std::format fmt shim below.
CPP_STD ?= $(C_STD_VER)

# The simulator flows exist to elaborate the RTL DUT; VL_DUT= on the command
# line still selects a model-only snapshot.
ifneq ($(USE_VCS)$(USE_XCELIUM),)
ifneq ($(and $(USE_VCS),$(USE_XCELIUM)),)
$(error USE_VCS and USE_XCELIUM are exclusive)
endif
VL_DUT ?= 1
endif

CXX_FLAGS = -m64 -std=$(CPP_STD) -g -Wfatal-errors -Wall -Wextra -Wpedantic -Wshadow -Wno-unused-variable -Wno-unused-parameter -pthread -DSC_CPLUSPLUS=201703L -DSC_INCLUDE_DYNAMIC_PROCESSES
# Boost.System is header-only since 1.69, and a2c's stacktrace use
# (q_assert.cpp) runs on the header-only backend (no BOOST_STACKTRACE_LINK)
# with identical output, needing only -ldl (already in LD_FLAGS below); Boost
# program_options is therefore the only Boost library actually linked.
# BOOST_LIBS names that link input; the container default below links the
# static site Boost in LD_BOOST, and a farm/pro layer can set BOOST_LIBS to
# link a shared Boost instead (see the LD_BOOST check above).
BOOST_LIBS ?= -lboost_program_options -L$(LD_BOOST)
LD_FLAGS = $(BOOST_LIBS) -L$(SYSTEMC_LIBDIR) -ldl -lrt -lsystemc
ifdef USE_XCELIUM
ifndef XCELIUM_TOOLS
$(error XCELIUM_TOOLS is not set - point it at the Xcelium install's tools directory to build with USE_XCELIUM)
endif
SYSTEMC_INCLUDE = $(XCELIUM_TOOLS)/systemc/include
endif
CPP_INCLUDES = -I$(BOOST_INCLUDE) -I$(SYSTEMC_INCLUDE) -I/usr/local/include

A2C_SRC_DIRS = $(A2C_ROOT)/common/systemc $(A2C_ROOT)/common/scmain $(wildcard $(A2C_ROOT)/interfaces/*) $(wildcard $(A2C_ROOT)/pro/interfaces/*)
# Project C++ source/include dirs come from the generated manifest (.gen/build.mk,
# included by a2c-common.mk) instead of globbing fixed functional roots; the
# per-dir file wildcards below pick up every .cpp within them.
PRJ_SRC_DIRS = $(A2C_SC_SRC_DIRS)

ifndef USE_GCC
CXX_FLAGS += -fstandalone-debug
else
CXX_FLAGS += -Wno-class-memaccess -Wno-aggressive-loop-optimizations -Wno-strict-aliasing
ifdef VL_DUT
CXX_FLAGS += -Wno-pedantic
endif
endif

# If not using c++23, use std::format shim and fmt library
ifneq ($(C_STD_VER), c++23)
CPP_INCLUDES += -I$(A2C_ROOT)/common/systemc/include/fmt
LD_FLAGS += -lfmt
endif

# Standard optimization source files.
CPP_SRC =

# Special optimization for some systemc files.
O3_CPP_SRC = $(A2C_ROOT)/common/systemc/logging.cpp $(A2C_ROOT)/common/systemc/bitTwiddling.cpp $(A2C_ROOT)/common/systemc/instanceFactory.cpp

# Extra compiler / linker dependencies (set by project Makefile)
A2C_SRC_DIRS += $(EXTRA_A2C_SRC_DIRS)
PRJ_SRC_DIRS += $(EXTRA_PRJ_SRC_DIRS)
CXX_FLAGS    += $(EXTRA_CXX_FLAGS)
CPP_SRC      += $(EXTRA_CPP_SRC)
O3_CPP_SRC   += $(EXTRA_O3_CPP_SRC)
CPP_INCLUDES += $(EXTRA_CPP_INCLUDES)
LD_FLAGS     += $(EXTRA_LD_FLAGS)

# Find all .cpp files in the A2C_SRC_DIRS and PRJ_SRC_DIRS directories.
CPP_SRC += $(foreach dir, $(A2C_SRC_DIRS), $(wildcard $(dir)/*.cpp))
CPP_SRC += $(foreach dir, $(PRJ_SRC_DIRS), $(wildcard $(dir)/*.cpp))

# C++20 module interface units include both generated files and user-authored
# .cppm files in project source directories. EXTRA_CPP_MODULE_SRC covers modules
# outside those directories. Scan the complete source set once per make parse
# into a Make include; this replaces the prior repeated $(shell sed ...) lookups
# that rescanned every module for every emitted compiler command.
# Source the manifest's full module set (A2C_CPP_MODULE_FILES), not SC_GEN_FILES:
# the gen set is now owned-only, but every imported module -- including foreign
# sub-project .cppm this build compiles but never regenerates -- must still be
# scanned so importers resolve their `import`s.
CPP_MODULE_CANDIDATES := $(sort \
	$(wildcard $(A2C_CPP_MODULE_FILES)) \
	$(foreach dir,$(A2C_SRC_DIRS),$(wildcard $(dir)/*.cppm)) \
	$(foreach dir,$(PRJ_SRC_DIRS),$(wildcard $(dir)/*.cppm)) \
	$(EXTRA_CPP_MODULE_SRC))
CPP_MODULE_MAP := $(GEN_BUILD_DIR)/cpp-modules.mk
CPP_MODULE_SCANNER := $(A2C_ROOT)/pysrc/gen_cpp_module_map.py
_CPP_MODULE_SCAN_STATUS := $(shell python3 "$(CPP_MODULE_SCANNER)" --output "$(CPP_MODULE_MAP)" $(CPP_MODULE_CANDIDATES) || echo failed)
ifneq ($(strip $(_CPP_MODULE_SCAN_STATUS)),)
$(error C++ module scan failed)
endif
include $(CPP_MODULE_MAP)

CPP_MODULE_SRC := $(foreach module,$(CPP_MODULE_NAMES),$(CPP_MODULE_PROVIDER_$(module)))
cpp_module_pcm = $(BUILD_DIR)/$(1:%.cppm=%.pcm)
cpp_module_src_for = $(CPP_MODULE_PROVIDER_$(1))
cpp_module_import_pcms = $(foreach imported,$(CPP_MODULE_IMPORTS_$(1)),$(if $(call cpp_module_src_for,$(imported)),$(call cpp_module_pcm,$(call cpp_module_src_for,$(imported)))))
# GCC has no standalone PCM: compiling the interface unit emits both the object
# and the module interface (CMI, in the default module cache). Inter-module
# ordering therefore hangs off the .module.o targets instead of .pcm targets.
cpp_module_obj = $(BUILD_DIR)/$(1:%.cppm=%.module.o)
cpp_module_import_objs = $(foreach imported,$(CPP_MODULE_IMPORTS_$(1)),$(if $(call cpp_module_src_for,$(imported)),$(call cpp_module_obj,$(call cpp_module_src_for,$(imported)))))

# CPP_MODULE_DEPS is what a consuming translation unit must wait for so the
# module interfaces it imports are available: standalone PCMs under Clang, or the
# module objects (which carry the CMIs) under GCC.
ifneq ($(strip $(CPP_MODULE_SRC)),)
ifdef USE_GCC
# GCC compiles each interface unit with -fmodules-ts, emitting the CMI into the
# default module cache keyed by module name. No -fmodule-file mapping is needed;
# imports resolve by name.
# -fno-module-lazy disables GCC's lazy CMI streaming. GCC 13.2 otherwise hits
# "recursive lazy load" when a module pulls in heavy standard headers (e.g.
# systemc.h -> <cmath> special functions) whose template instantiations re-enter
# the loader. Must be applied uniformly across the whole import graph.
CXX_FLAGS += -fmodules-ts -fno-module-lazy
CPP_MODULE_DEPS = $(CPP_MODULE_OBJ)
else
CXX_FLAGS += $(CPP_MODULE_FLAGS)
CPP_MODULE_DEPS = $(CPP_MODULE_PCM)
endif
else
CPP_MODULE_DEPS =
endif

ifdef VL_DUT
# Wrapper include dirs come from the manifest. The `_verif` registrations live in
# the per-assembler VlRegistrar.cpp files discovered under A2C_SC_SRC_DIRS, so
# there is no vl_wrap aggregator entry to compile here.
CPP_INCLUDES += $(foreach dir, $(A2C_VL_WRAP_DIRS), -I$(dir))
ifdef USE_VCS
# The `-sc_model` shell headers the VlRegistrar #includes land under csrc in VCS_RUNDIR.
CPP_INCLUDES += -I$(VCS_RUNDIR)/csrc/sysc/include -I$(VCS_HOME)/include
else ifdef USE_XCELIUM
# The foreign-module shells the VlRegistrar #includes are generated under .gen/vl.
CPP_INCLUDES += -I$(A2C_VL_GEN_INC)
else
# Each Verilated top is built into its own --Mdir (A2C_VL_BUILD_DIR/obj_dir/<top>)
# by a2c-vl-wrap.mk; its V<top>.h is a build output the VlRegistrar #includes.
# Add each per-top Mdir to the include path, records-driven from A2C_VL_TOPS.
CPP_INCLUDES += $(foreach top, $(A2C_VL_TOPS), -I$(A2C_VL_BUILD_DIR)/obj_dir/$(top))
CPP_INCLUDES += -I$(VERILATOR_ROOT)/include -I$(VERILATOR_ROOT)/include/vltstd
endif
endif

ifdef USE_XCELIUM
CPP_INCLUDES += -I$(XCELIUM_TOOLS)/systemc/include/cci -I$(XCELIUM_TOOLS)/systemc/include/factory \
	-I$(XCELIUM_TOOLS)/systemc/include/tlm2 -I$(XCELIUM_TOOLS)/include -I$(XCELIUM_TOOLS)/inca/include
endif

# All include directories.
CPP_INCLUDES += $(foreach dir, $(A2C_SRC_DIRS), -I$(dir))
CPP_INCLUDES += $(foreach dir, $(PRJ_SRC_DIRS), -I$(dir))

# Put all auto generated stuff to this build dir. BIN_DIR comes from a2c-common.mk
# so that `clean` owns it from either directory.
BIN = run
ifneq ($(USE_VCS)$(USE_XCELIUM),)
# VCS and Xcelium elaborate the SystemC/HDL topology into the snapshot, so each
# DUT topology (see a2c-vcs.mk, a2c-xrun.mk) is its own snapshot and binary:
# run_<inst>_<type>[_tandem], or run_model when no RTL instance is elaborated
# (VL_INST= on the command line keeps the compiled objects of a VL_DUT build).
ifdef VL_DUT
VL_INST ?= $(HDL_TOP_MODULE)
endif
VL_TYPE ?= verif
VL_TANDEM ?= 0
DUT_TOPOLOGY ?= $(if $(VL_INST),$(VL_INST)_$(VL_TYPE)$(if $(filter 1,$(VL_TANDEM)),_tandem),model)
BIN = run_$(DUT_TOPOLOGY)
# Both simulators run sc_main up to its first sc_start to elaborate the
# topology, so the snapshot build needs the testbench command line the
# snapshot is later run with.
DUT_TESTBENCH ?= $(HDL_TOP_MODULE)
DUT_ELAB_ARGS ?= $(DUT_TESTBENCH) $(if $(VL_INST),--vlInst $(VL_INST) --vlType $(VL_TYPE)) $(if $(filter 1,$(VL_TANDEM)),--vlTandem)
# Regression snapshots, one entry per block: <inst>:<type>[:tandem][,<type>[:tandem]]...
# e.g. debayer:verif,verif:tandem,model:tandem. Regression files pass one
# DUT_TOPOLOGIES+=<entry> per block on the build command line. Every test that
# instantiates no RTL runs on run_model. See vcs_snapshots and xrun_snapshots.
DUT_TOPOLOGIES ?= $(HDL_TOP_MODULE):verif,verif:tandem
comma := ,
dut_topology_inst = $(firstword $(subst :, ,$(1)))
dut_topology_expand = $(addprefix $(call dut_topology_inst,$(1)):,$(subst $(comma), ,$(patsubst $(call dut_topology_inst,$(1)):%,%,$(1))))
DUT_TOPOLOGY_LIST = $(foreach t,$(DUT_TOPOLOGIES),$(call dut_topology_expand,$(t)))
dut_topology_words = $(subst :, ,$(1))
dut_topology_make = $(MAKE) VL_INST=$(word 1,$(call dut_topology_words,$(1))) VL_TYPE=$(word 2,$(call dut_topology_words,$(1))) VL_TANDEM=$(if $(word 3,$(call dut_topology_words,$(1))),1,0)
endif
BUILD_DIR = $(BIN_DIR)/$(PROJECTNAME).build
# Whole-design verilation build-output dir: holds the per-top obj_dir/<top> Mdirs
# and the single lib<proj>vl_s_wrap.a. A fixed tooling location under the build
# tree (not a manifest fact), so `clean` removing BIN_DIR removes it too.
A2C_VL_BUILD_DIR = $(BIN_DIR)/vl

# Add to compiler dependencies
CXX_FLAGS += $(CPP_INCLUDES)

# VCS selects the simulator glue in main.cpp; VCS_DUT additionally selects the
# vlogan shell class as the `_verif` DUT in the VlRegistrar and SC wrapper.
ifdef USE_VCS
CXX_FLAGS += -DVCS
ifdef VL_DUT
CXX_FLAGS += -DVCS_DUT
endif
endif

# XCELIUM selects the simulator glue in main.cpp; XCELIUM_DUT selects the
# foreign-module shell as the `_verif` DUT in the VlRegistrar. The Cadence
# defines are what xmsc passes to its own compiler; -fPIC because xrun links
# the objects into a shared library.
ifdef USE_XCELIUM
CXX_FLAGS += -DXCELIUM -DNCSC -DCADENCE -DLNX86 -DXMSC -D_GLIBCXX_USE_CXX11_ABI=1 -fPIC \
	-Wno-undefined-var-template -Wno-deprecated-declarations -Wno-mismatched-tags
ifdef VL_DUT
CXX_FLAGS += -DXCELIUM_DUT
endif
endif

ifdef VL_DUT
ifndef USE_VCS
ifndef USE_XCELIUM
CXX_FLAGS += -DVERILATOR
LD_FLAGS += -L$(A2C_VL_BUILD_DIR) -l$(PROJECTNAME)vl_s_wrap -latomic
# The linked-in verilated library is a build output of the vl sub-make, so name it
# as a prerequisite: a re-verilate that leaves every generated V<top>.h alone
# would otherwise not relink, and the binary would keep the previous RTL.
# Wildcard-filtered because the sub-make has not run on a cold tree, where the
# binary does not exist either and links fresh.
VL_WRAP_LIB = $(wildcard $(A2C_VL_BUILD_DIR)/lib$(PROJECTNAME)vl_s_wrap.a)
# https://github.com/verilator/verilator/issues/5672
CXX_FLAGS += -Wno-sign-compare
endif
endif
endif

# These module lists and flags are invariant for one make parse. Materialize
# them after BUILD_DIR and all conditional CXX_FLAGS are known so every emitted
# compiler command reuses the values instead of rebuilding the full strings.
CPP_MODULE_PCM := $(CPP_MODULE_SRC:%.cppm=$(BUILD_DIR)/%.pcm)
CPP_MODULE_OBJ := $(CPP_MODULE_SRC:%.cppm=$(BUILD_DIR)/%.module.o)
CPP_MODULE_FLAGS := $(foreach module,$(CPP_MODULE_NAMES),-fmodule-file=$(module)=$(call cpp_module_pcm,$(call cpp_module_src_for,$(module))))
CPP_MODULE_OBJ_FLAGS := $(filter-out -I%,$(CXX_FLAGS))

# Build-flavor stamp. The model and VL (VL_DUT=1) builds share the same
# BIN/BUILD_DIR paths and the same object files; toggling VL_DUT only changes the
# compile/link flags (adds -DVERILATOR and the vl wrapper lib). Timestamps cannot
# see that flag flip, so `make all` after `make all VL_DUT=1` (or the reverse)
# would otherwise reuse objects built for the other flavor and run a mismatched
# binary (e.g. a model binary against a verif DUT -> unregistered <block>_verif).
# This stamp records the current flavor; the parse-time shell rewrites it only on
# a mismatch, so its mtime bumps only on an actual flip. Listing it as a
# prerequisite of every flag-carrying compile rule forces just the affected
# objects to recompile (and the binary to relink) on a flip, without changing any
# output path that downstream consumers of build/run depend on.
BUILD_FLAVOR := $(if $(USE_VCS),vcs-,)$(if $(USE_XCELIUM),xrun-,)$(if $(VL_DUT),vl,model)
FLAVOR_STAMP := $(BUILD_DIR)/.build_flavor
$(shell mkdir -p $(BUILD_DIR); [ "$$(cat $(FLAVOR_STAMP) 2>/dev/null)" = "$(BUILD_FLAVOR)" ] || printf '%s\n' "$(BUILD_FLAVOR)" > $(FLAVOR_STAMP))

#------------------------------------------------------------------------
# Systemc build file based targets
#------------------------------------------------------------------------

# main receipe to build the binary

# All .o files go to build dir.
OBJ = $(CPP_SRC:%.cpp=$(BUILD_DIR)/%.o)
OBJ += $(CPP_MODULE_OBJ)
# Gcc/Clang will create these .d files containing dependencies.
DEP = $(OBJ:%.o=%.d)
# Clang emits a .d beside each PCM; GCC's module .d comes from the .module.o and
# is already covered by $(OBJ:%.o=%.d) above.
ifndef USE_GCC
DEP += $(CPP_MODULE_PCM:%.pcm=%.d)
endif

# Actual target of the binary - depends on all .o files and, under VL_DUT, on the
# verilated library LD_FLAGS links in. Only the objects are named on the command
# line; the library reaches the link through -l.
$(BIN_DIR)/$(BIN) : $(OBJ) $(VL_WRAP_LIB)
ifndef USE_VCS
ifndef USE_XCELIUM
    # Create build directories - same structure as sources.
	mkdir -p $(@D)
    # Just link all the object files.
	$(CXX) -o $@ $(OBJ) $(LD_FLAGS)
endif
endif

# Rule to compile files in O3_CPP_SRC to add -o3 optimization
$(O3_CPP_SRC:%.cpp=$(BUILD_DIR)/%.o): $(BUILD_DIR)/%.o: %.cpp $(CPP_MODULE_DEPS) $(FLAVOR_STAMP)
	mkdir -p $(@D)
	$(CXX) -O3 $(CXX_FLAGS) -MMD -MP -c $< -o $@

# Rule to compile all other .cpp files
# -MMD writes a .d file beside the .o; -MP adds a phony target per header it
# names, so a header that a later build no longer produces (a simulator shell
# after `clean`, a deleted source) does not stop the build.
$(BUILD_DIR)/%.o : %.cpp $(CPP_MODULE_DEPS) $(FLAVOR_STAMP)
	mkdir -p $(@D)
	$(CXX) $(CXX_FLAGS) -MMD -MP -c $< -o $@

# Rules to build generated C++20 module interfaces to linkable objects. Clang
# precompiles each interface to a PCM and then compiles that PCM to an object;
# GCC does both in a single step and writes the CMI to the module cache. The
# import-ordering edges below apply to whichever artifact the active compiler
# produces (CPP_MODULE_DEPS): .pcm for Clang, .module.o for GCC.
ifndef USE_GCC

# Clang: precompile the interface unit to a PCM, then compile the PCM to an
# object. The module flags are supplied at both stages because an interface may
# import another generated interface.
$(BUILD_DIR)/%.pcm : %.cppm $(FLAVOR_STAMP)
	mkdir -p $(@D)
	$(CXX) $(CXX_FLAGS) -MMD -MP --precompile -x c++-module $< -o $@

$(foreach module,$(CPP_MODULE_NAMES),$(eval $(call cpp_module_pcm,$(call cpp_module_src_for,$(module))): $(call cpp_module_import_pcms,$(module))))

# A block-module unit (`<block>.cppm`) includes its `<block>Base.h` in the
# global module fragment, and that header `import`s the block's context types
# module. The module scanner sees only the .cppm's own `import` lines, so that
# transitive dependency is invisible to the edge above. Order every
# block-module pcm after all context (`*Includes.cppm`) pcms; the context
# modules' own inter-dependencies are already captured by the import-name scan.
CPP_CONTEXT_MODULE_PCM = $(foreach src,$(filter %Includes.cppm,$(CPP_MODULE_SRC)),$(call cpp_module_pcm,$(src)))
$(foreach src,$(filter-out %Includes.cppm,$(CPP_MODULE_SRC)),$(eval $(call cpp_module_pcm,$(src)): $(CPP_CONTEXT_MODULE_PCM)))

.SECONDARY: $(CPP_MODULE_PCM)

$(BUILD_DIR)/%.module.o : $(BUILD_DIR)/%.pcm
	mkdir -p $(@D)
	$(CXX) $(CPP_MODULE_OBJ_FLAGS) -c $< -o $@

else

# GCC: one step compiles the interface unit to its object and emits the CMI into
# the module cache (keyed by module name). Full CXX_FLAGS are used because the
# interface's global module fragment includes headers (e.g. `<block>Base.h`).
$(BUILD_DIR)/%.module.o : %.cppm $(FLAVOR_STAMP)
	mkdir -p $(@D)
	$(CXX) $(CXX_FLAGS) -MMD -MP -x c++ -c $< -o $@

# Same ordering as the Clang path, expressed over the .module.o targets since
# GCC produces the CMI as a side effect of the object compile.
$(foreach module,$(CPP_MODULE_NAMES),$(eval $(call cpp_module_obj,$(call cpp_module_src_for,$(module))): $(call cpp_module_import_objs,$(module))))
CPP_CONTEXT_MODULE_OBJ = $(foreach src,$(filter %Includes.cppm,$(CPP_MODULE_SRC)),$(call cpp_module_obj,$(src)))
$(foreach src,$(filter-out %Includes.cppm,$(CPP_MODULE_SRC)),$(eval $(call cpp_module_obj,$(src)): $(CPP_CONTEXT_MODULE_OBJ)))

endif

# Include all .d files
-include $(DEP)

ifdef USE_VCS
include $(A2C_ROOT)/include/make/a2c-vcs.mk
endif
ifdef USE_XCELIUM
include $(A2C_ROOT)/include/make/a2c-xrun.mk
endif

#------------------------------------------------------------------------
# Systemc build phony targets
#------------------------------------------------------------------------

.PHONY : all clean
.DEFAULT_GOAL = all

all: gen
ifdef VL_DUT
ifndef USE_VCS
ifndef USE_XCELIUM
	mkdir -p $(A2C_VL_BUILD_DIR) && $(MAKE) -C $(A2C_VL_BUILD_DIR) -f $(A2C_ROOT)/include/make/a2c-vl-build-entry.mk vlwrap REPO_ROOT=$(REPO_ROOT)
endif
endif
endif
	$(MAKE) $(BIN_DIR)/$(BIN)

clean::
	$(RM) -rf simx.*
	# GCC C++20 module cache, written to the make working directory.
	$(RM) -rf gcm.cache

help::
	@echo "  all     	- Build the project binary"
	@echo "  compdb  	- Generate compile_commands.json for clangd"
	@echo "  clangd  	- Generate .clangd configuration for IDE"
	@echo "Makefile Runtime Variables:"
	@echo "  VL_DUT=1	- Build verilator wrapper for the DUT instances"
	@echo "  USE_VCS=1	- Compile for VCS and link with vcs (with VL_DUT=1: RTL DUT elaborated by VCS)"
	@echo "  USE_XCELIUM=1	- Compile for Xcelium and build its snapshot with xrun (with VL_DUT=1: RTL DUT elaborated by Xcelium)"

#------------------------------------------------------------------------
# Generate compile_commands.json for clangd/OpenCode
#------------------------------------------------------------------------

# Capture only the object graph: generation and linking do not contribute C++
# compilation database entries. The normal pass already covers every C++ source.
# A second VL_DUT pass is useful only when a wrapper directory contains a
# compiled .cpp source whose command needs -DVERILATOR; generated wrapper headers
# and SystemVerilog files do not create compile_commands entries.
.PHONY: compdb-capture
compdb-capture: $(OBJ)

COMPDB_VL_CPP_SRC := $(foreach dir,$(A2C_VL_WRAP_DIRS),$(wildcard $(dir)/*.cpp))
ifeq ($(strip $(COMPDB_VL_CPP_SRC)),)
COMPDB_VL_CAPTURE =
COMPDB_MAKE_N_FILES = $(GEN_BUILD_DIR)/compdb.model.make-n.txt
else
COMPDB_VL_CAPTURE = $(MAKE) -n -B compdb-capture VL_DUT=1 > $(GEN_BUILD_DIR)/compdb.vl.make-n.txt \
	|| { echo "compdb: VL dry-run failed; building compile DB from the model pass only"; : > $(GEN_BUILD_DIR)/compdb.vl.make-n.txt; }
COMPDB_MAKE_N_FILES = $(GEN_BUILD_DIR)/compdb.model.make-n.txt $(GEN_BUILD_DIR)/compdb.vl.make-n.txt
endif

.PHONY: compdb
compdb:
	@mkdir -p $(GEN_BUILD_DIR)
	@$(MAKE) -n -B compdb-capture > $(GEN_BUILD_DIR)/compdb.model.make-n.txt
	@$(COMPDB_VL_CAPTURE)
	@python3 $(A2C_ROOT)/pysrc/gen_compile_commands.py \
		$(COMPDB_MAKE_N_FILES) \
		$(REPO_ROOT)/compile_commands.json \
		--directory $(PROJECT_RUNDIR) >/dev/null
	@echo "Generated $(REPO_ROOT)/compile_commands.json"

#------------------------------------------------------------------------
# Generate .clangd configuration for IDE
#------------------------------------------------------------------------
.PHONY: clangd
clangd: compdb
	@echo "Generating .clangd configuration..."
	@( \
		echo "# Auto-generated from Makefile - DO NOT EDIT MANUALLY"; \
		echo "# Regenerate with: make clangd"; \
		echo ""; \
		echo "CompileFlags:"; \
		echo "  Add:"; \
		for flag in $(filter-out -m% -Wfatal-errors -g -fmodule-file=% $(CPP_INCLUDES), $(CXX_FLAGS)); do \
			echo "    - $$flag"; \
		done; \
		for inc in $(CPP_INCLUDES); do \
			echo "    - $$inc"; \
		done; \
		echo "  Compiler: clang++"; \
		echo "  Remove:"; \
		echo "    - -m*"; \
		echo "    - -W*fatal-errors"; \
		echo "    - -fmodule-file=*"; \
		echo ""; \
		echo "Diagnostics:"; \
		echo "  Suppress:"; \
		echo "    - module_unimported_use"; \
		echo "  UnusedIncludes: None"; \
		echo ""; \
		echo "InlayHints:"; \
		echo "  Enabled: Yes"; \
		echo "  ParameterNames: Yes"; \
		echo "  DeducedTypes: Yes"; \
		echo ""; \
		echo "Hover:"; \
		echo "  ShowAKA: Yes"; \
	) > $(REPO_ROOT)/.clangd
	@echo "Generated $(REPO_ROOT)/.clangd"
	@echo "Reload your IDE to apply changes"
