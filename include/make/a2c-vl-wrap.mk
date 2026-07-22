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

# Verilated tops come from the build manifest's per-top records (A2C_VL_TOPS +
# A2C_VL_{SV,INCDIRS,OBJ}_<top>), not from a filename scan. Each record names its
# design unit and archived object explicitly, so nothing is derived with
# $(notdir) and the library is not globbed. The .svh body is never a record (a
# default-less parameterized module cannot be a Verilated top). The verilated
# object dir stays under A2C_VL_BUILD_DIR (this make runs with that as cwd) so
# the generated <block>_hdl_sc_wrapper.h finds V<top>.h on the SystemC -Iobj_dir.
VL_OBJ_FILES = $(foreach t,$(A2C_VL_TOPS),obj_dir/$(A2C_VL_OBJ_$(t)))

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

# One verilate per recorded top: the explicit design unit (--top), the recorded
# physical .sv, and the recorded include search path (so a trampoline finds the
# `include`d canonical `_hdl_sv_wrapper.svh` body wherever it lives, including a
# reused child's own vl_wrap dir).
define vl_top_rule
obj_dir/$(A2C_VL_OBJ_$(1)): $(VL_GEN_SV_FILES)
	verilator $(VERILATOR_OPTS) -CFLAGS $(VERILATOR_CFLAG_OPTS) -F $(A2C_ROOT)/common/systemVerilog/a2c.f -F $(REPO_ROOT)/rtl/rtl.f $(A2C_SV_FILES) $(addprefix +incdir+,$(A2C_VL_INCDIRS_$(1))) $(A2C_VL_SV_$(1)) -top $(1)
endef
$(foreach t,$(A2C_VL_TOPS),$(eval $(call vl_top_rule,$(t))))

lib$(PROJECTNAME)vl_s_wrap.a: obj_dir/Vvl_dummy $(VL_OBJ_FILES)
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
