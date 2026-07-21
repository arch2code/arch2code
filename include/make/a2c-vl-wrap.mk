#------------------------------------------------------------------------
# Check mandatory variables are set when including this makefile
#------------------------------------------------------------------------

ifndef REPO_ROOT
$(error REPO_ROOT is not set - please set to the root of your repository)
endif
ifndef PROJECTNAME
$(error PROJECTNAME is not set - please set to the name of your project)
endif
ifndef VL_SRC_DIRS
$(error VL_SRC_DIRS is not set - please set to the directory containing your wrapper source files to be verilated)
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

VL_GEN_SV_FILES += $(call find_gen_sv_sources, $(VL_SRC_DIRS))
VL_GEN_SC_FILES += $(call find_gen_cpp_sources, $(VL_SRC_DIRS))

# Only .sv files become Verilated tops. A generated canonical wrapper body
# (.svh) is maintained by the generation scan and `include`d by variant
# trampolines, but is never a top (a default-less parameterized module cannot be
# a top); filter it out so it never becomes a malformed object target.
VL_OBJ_FILES = $(subst ./,obj_dir/V, $(patsubst %.sv, %.o, $(filter %.sv, $(VL_GEN_SV_FILES))))

VL_LIB_OBJ_FILES = obj_dir/verilated.o obj_dir/verilated_dpi.o obj_dir/verilated_vcd_c.o obj_dir/verilated_threads.o

ifdef VL_COV
VL_LIB_OBJ_FILES += obj_dir/verilated_cov.o
endif

#------------------------------------------------------------------------
# Systemc build file based targets
#------------------------------------------------------------------------

# Compile verilator common objects (verilated_dpi.o, verilated_vcd_c.o, verilated_threads.o)
obj_dir/Vvl_dummy: $(VL_GEN_SV_FILES) $(GEN_DEPS)
	verilator $(VERILATOR_OPTS) -CFLAGS $(VERILATOR_CFLAG_OPTS) $(A2C_ROOT)/common/verilator/vl_dummy.sv $(A2C_ROOT)/common/verilator/vl_dummy.cpp --top vl_dummy -exe

# +incdir for the wrapper's own directory so a variant trampoline finds its
# co-located `_hdl_sv_wrapper.svh` body. Wrappers mirror the YAML/source layout,
# so the body may live in a per-block subdirectory; for the flat layout this
# directory is the Verilator cwd and the +incdir is a harmless no-op.
$(VL_OBJ_FILES): $(VL_GEN_SV_FILES)
	verilator $(VERILATOR_OPTS) -CFLAGS $(VERILATOR_CFLAG_OPTS) -F $(A2C_ROOT)/common/systemVerilog/a2c.f -F $(REPO_ROOT)/rtl/rtl.f $(A2C_SV_FILES) +incdir+$(dir $(subst obj_dir/V,, $(patsubst %.o, %.sv, $@))) $(subst obj_dir/V,, $(patsubst %.o, %.sv, $@)) -top $(notdir $(subst obj_dir/V,, $(patsubst %.o,%, $@)))

lib$(PROJECTNAME)vl_s_wrap.a: obj_dir/Vvl_dummy $(VL_OBJ_FILES)
	ar -rcs $@ $(VL_LIB_OBJ_FILES) obj_dir/V*_hdl_sv_wrapper*.o

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
