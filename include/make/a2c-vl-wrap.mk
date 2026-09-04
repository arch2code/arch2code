#------------------------------------------------------------------------
# Check mandatory variables are set when including this makefile
#------------------------------------------------------------------------

ifndef REPO_ROOT
$(error REPO_ROOT is not set - please set to the root of your repository)
endif
ifndef PROJECTNAME
$(error PROJECTNAME is not set - please set to the name of your project)
endif

#------------------------------------------------------------------------
# Systemc build global variables
#------------------------------------------------------------------------

VERILATOR_OPTS = -sc -sv --trace --trace-structs --trace-params --pins-bv 2 --no-timing --build -Wno-fatal -j 4 -DVL_DUT -MMD
VERILATOR_CFLAG_OPTS = '-std=$(C_STD_VER) -DSC_CPLUSPLUS=201703L -DSC_INCLUDE_DYNAMIC_PROCESSES'

ifdef VL_COV
VERILATOR_OPTS += --coverage
endif

VERILATOR_OPTS += $(VERILATOR_USER_OPTS)

# Design SV inputs of a verilate run: the manifest's DB-derived set plus the
# user-hosted generated-region SV the manifest never lists, the same seam
# a2c-common.mk layers for generation. Wildcard-filtered because the manifest
# records intent while `make newmodule` scaffolds on disk, so a not-yet-created
# file must not become a missing prerequisite. This is the floor under the
# per-top records below, which are the only place the framework and transitive
# `include`s appear.
VL_SV_DEPS = $(wildcard $(A2C_SV_DEP_FILES) $(EXTRA_SV_GEN_FILES))

VL_DUMMY_SRC = $(A2C_ROOT)/common/verilator/vl_dummy.sv $(A2C_ROOT)/common/verilator/vl_dummy.cpp

# Verilator's -MMD record of what a verilate actually read. Its targets are the
# generated V<top>.* sources, not the object, so the prerequisite list is lifted
# out and re-hung below: obj_dir/ words are those targets (relative because
# --Mdir below is), `:` separates, `\` wraps. An absent record yields nothing,
# correct on a cold tree where the object is missing anyway.
vl_dep_prereqs = $(filter-out : \ obj_dir/%,$(file <obj_dir/$(1)/V$(1)__ver.d))

# Empty recipe per recorded prerequisite: a file the record names but a later
# release deleted forces one re-verilate instead of failing the build.
VL_DEP_PREREQS := $(sort $(foreach t,vl_dummy $(A2C_VL_TOPS),$(call vl_dep_prereqs,$(t))))
ifneq ($(VL_DEP_PREREQS),)
$(VL_DEP_PREREQS): ;
endif

# Verilated tops come from the build manifest's per-top records (A2C_VL_TOPS +
# A2C_VL_SV_<top>), not from a filename scan. Each record names its design unit
# and physical wrapper explicitly, so nothing is derived with $(notdir) and the
# library is not globbed. The verilator object name follows verilator's
# V<top>__ALL.o convention, reconstructed here rather than carried in the
# manifest. The .svh body is never a record (a default-less parameterized module
# cannot be a Verilated top). Each top gets its OWN --Mdir (obj_dir/<top>) so
# concurrent verilate runs never write a shared obj_dir; the per-assembler
# VlRegistrar picks up each V<top>.h from its own Mdir on the SystemC include
# path (a2c-systemc.mk drives that from A2C_VL_TOPS).
VL_OBJ_FILES = $(foreach t,$(A2C_VL_TOPS),obj_dir/$(t)/V$(t)__ALL.o)

VL_LIB_OBJ_FILES = obj_dir/vl_dummy/verilated.o obj_dir/vl_dummy/verilated_dpi.o obj_dir/vl_dummy/verilated_vcd_c.o obj_dir/vl_dummy/verilated_threads.o

ifdef VL_COV
VL_LIB_OBJ_FILES += obj_dir/vl_dummy/verilated_cov.o
endif

#------------------------------------------------------------------------
# Systemc build file based targets
#------------------------------------------------------------------------

# Compile the verilator common runtime objects (verilated.o, verilated_dpi.o,
# verilated_vcd_c.o, verilated_threads.o) into their own Mdir. Framework sources
# only: verilator leaves the target untouched when nothing changed, so a
# generated-source stamp prerequisite would keep this rule permanently out of date.
obj_dir/vl_dummy/Vvl_dummy: $(VL_DUMMY_SRC) $(call vl_dep_prereqs,vl_dummy)
	mkdir -p obj_dir/vl_dummy
	verilator $(VERILATOR_OPTS) --Mdir obj_dir/vl_dummy -CFLAGS $(VERILATOR_CFLAG_OPTS) $(VL_DUMMY_SRC) --top vl_dummy -exe

# One verilate per recorded top into its own --Mdir: the explicit design unit
# (--top), the recorded physical .sv, and the recorded include search path (so a
# trampoline finds the `include`d canonical `_hdl_sv_wrapper.svh` body wherever
# it lives, including a reused child's own vl_wrap dir).
define vl_top_rule
obj_dir/$(1)/V$(1)__ALL.o: $(VL_SV_DEPS) $(call vl_dep_prereqs,$(1))
	mkdir -p obj_dir/$(1)
	verilator $(VERILATOR_OPTS) --Mdir obj_dir/$(1) -CFLAGS $(VERILATOR_CFLAG_OPTS) -F $(A2C_ROOT)/common/systemVerilog/a2c.f -F $(A2C_RTL_DOT_F) $(A2C_SV_FILES) $(addprefix +incdir+,$(A2C_VL_WRAP_DIRS)) $(A2C_VL_SV_$(1)) -top $(1)
endef
$(foreach t,$(A2C_VL_TOPS),$(eval $(call vl_top_rule,$(t))))

lib$(PROJECTNAME)vl_s_wrap.a: obj_dir/vl_dummy/Vvl_dummy $(VL_OBJ_FILES)
	ar -rcs $@ $(VL_LIB_OBJ_FILES) $(VL_OBJ_FILES)

#------------------------------------------------------------------------
# Systemc build phony targets
#------------------------------------------------------------------------

.PHONY : all clean
.DEFAULT_GOAL := all

vlwrap: lib$(PROJECTNAME)vl_s_wrap.a

all : gen
	$(MAKE) vlwrap

clean::
	rm -rf lib*vl_s_wrap.a obj_dir/


help::
	@echo "  all     	- Build the verilator wrapper library"
