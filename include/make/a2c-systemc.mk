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
ifndef SYSTEMC_INCLUDE
$(error SYSTEMC_INCLUDE is not set - please set to systemc-2.3.4 <install directory>/include)
endif
ifndef SYSTEMC_LIBDIR
$(error SYSTEMC_LIBDIR is not set - please set to systemc-2.3.4 <install directory>/lib)
endif
ifndef BOOST_INCLUDE
$(error BOOST_INCLUDE is not set - please set to boost library <install directory>/include)
endif
ifndef LD_BOOST
$(error LD_BOOST is not set - please set to boost library (.so) path)
endif

ifndef VERILATOR_ROOT
VERILATOR_ROOT=/usr/local/share/verilator
endif

#------------------------------------------------------------------------
# Systemc build global variables
#------------------------------------------------------------------------

CXX_FLAGS = -m64 -std=$(C_STD_VER) -g -Wfatal-errors -Wall -Wextra -Wpedantic -Wshadow -Wno-unused-variable -Wno-unused-parameter -pthread -DBOOST_STACKTRACE_LINK -DSC_CPLUSPLUS=201703L -DSC_INCLUDE_DYNAMIC_PROCESSES
LD_FLAGS = -lboost_system -lboost_program_options -lboost_stacktrace_basic -L$(LD_BOOST) -L$(SYSTEMC_LIBDIR) -ldl -lrt -lsystemc
CPP_INCLUDES = -I$(BOOST_INCLUDE) -I$(SYSTEMC_INCLUDE) -I/usr/local/include

A2C_SRC_DIRS = $(A2C_ROOT)/common/systemc $(A2C_ROOT)/common/scmain $(wildcard $(A2C_ROOT)/interfaces/*) $(wildcard $(A2C_ROOT)/pro/interfaces/*)
PRJ_SRC_DIRS = $(call find_cpp_source_directories, $(REPO_ROOT)/base $(REPO_ROOT)/model $(REPO_ROOT)/fw $(REPO_ROOT)/tb)

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

# Generated C++20 module interface units.  Consumers import these by module
# name, so precompile them before compiling any C++ translation units and pass
# the resulting PCM files explicitly to Clang.
CPP_MODULE_SRC = $(filter %.cppm,$(SC_GEN_FILES))
cpp_module_name = $(basename $(notdir $(1:Includes.cppm=.cppm)))
cpp_module_pcm = $(BUILD_DIR)/$(1:%.cppm=%.pcm)
cpp_module_src_for = $(firstword $(foreach src,$(CPP_MODULE_SRC),$(if $(filter $(1),$(call cpp_module_name,$(src))),$(src))))
cpp_module_import_names = $(shell test -f "$(1)" && sed -n 's/^[[:space:]]*import[[:space:]]\+\([A-Za-z_][A-Za-z0-9_]*\)[[:space:]]*;.*/\1/p' "$(1)" || true)
cpp_module_import_pcms = $(foreach module,$(call cpp_module_import_names,$(1)),$(if $(call cpp_module_src_for,$(module)),$(call cpp_module_pcm,$(call cpp_module_src_for,$(module)))))
CPP_MODULE_PCM = $(CPP_MODULE_SRC:%.cppm=$(BUILD_DIR)/%.pcm)
CPP_MODULE_OBJ = $(CPP_MODULE_SRC:%.cppm=$(BUILD_DIR)/%.module.o)
CPP_MODULE_FLAGS = $(foreach src,$(CPP_MODULE_SRC),-fmodule-file=$(call cpp_module_name,$(src))=$(call cpp_module_pcm,$(src)))
CPP_MODULE_OBJ_FLAGS = $(filter-out -I%,$(CXX_FLAGS))

ifneq ($(strip $(CPP_MODULE_SRC)),)
ifndef USE_GCC
CXX_FLAGS += $(CPP_MODULE_FLAGS)
else
$(error Generated C++20 module interface units require Clang; unset USE_GCC)
endif
endif

ifdef VL_DUT
CPP_SRC += $(REPO_ROOT)/verif/vl_wrap/vl_wrap.cpp
CPP_INCLUDES += $(foreach dir, $(call find_cpp_source_directories, $(REPO_ROOT)/verif/vl_wrap), -I$(dir))
CPP_INCLUDES += -I$(VERILATOR_ROOT)/include -I$(VERILATOR_ROOT)/include/vltstd
endif

# All include directories.
CPP_INCLUDES += $(foreach dir, $(A2C_SRC_DIRS), -I$(dir))
CPP_INCLUDES += $(foreach dir, $(PRJ_SRC_DIRS), -I$(dir))

# Put all auto generated stuff to this build dir.
BIN = run
BIN_DIR = $(PROJECT_RUNDIR)/build
BUILD_DIR = $(BIN_DIR)/$(PROJECTNAME).build

# Add to compiler dependencies
CXX_FLAGS += $(CPP_INCLUDES)

ifdef VL_DUT
ifndef USE_VCS
CXX_FLAGS += -DVERILATOR
LD_FLAGS += -L$(REPO_ROOT)/verif/vl_wrap -l$(PROJECTNAME)vl_s_wrap -latomic
# https://github.com/verilator/verilator/issues/5672
CXX_FLAGS += -Wno-sign-compare
endif
endif

#------------------------------------------------------------------------
# Systemc build file based targets
#------------------------------------------------------------------------

# main receipe to build the binary

# All .o files go to build dir.
OBJ = $(CPP_SRC:%.cpp=$(BUILD_DIR)/%.o)
OBJ += $(CPP_MODULE_OBJ)
# Gcc/Clang will create these .d files containing dependencies.
DEP = $(OBJ:%.o=%.d)
DEP += $(CPP_MODULE_PCM:%.pcm=%.d)

# Actual target of the binary - depends on all .o files.
$(BIN_DIR)/$(BIN) : $(OBJ)
ifndef USE_VCS
    # Create build directories - same structure as sources.
	mkdir -p $(@D)
    # Just link all the object files.
	$(CXX) -o $@ $^ $(LD_FLAGS)
endif

# Rule to compile files in O3_CPP_SRC to add -o3 optimization
$(O3_CPP_SRC:%.cpp=$(BUILD_DIR)/%.o): $(BUILD_DIR)/%.o: %.cpp
	mkdir -p $(@D)
	$(CXX) -O3 $(CXX_FLAGS) -MMD -c $< -o $@

# Rule to compile all other .cpp files
# The -MMD flags additionaly creates a .d file with the same name as the .o file.
$(BUILD_DIR)/%.o : %.cpp $(GEN_DB_DEPS) $(CPP_MODULE_PCM)
	mkdir -p $(@D)
	$(CXX) $(CXX_FLAGS) -MMD -c $< -o $@

# Rules to precompile generated C++20 module interfaces and compile PCMs to
# linkable objects.  The module flags are supplied at both stages because an
# interface may import another generated interface.
$(BUILD_DIR)/%.pcm : %.cppm $(GEN_DB_DEPS)
	mkdir -p $(@D)
	$(CXX) $(CXX_FLAGS) -MMD --precompile -x c++-module $< -o $@

$(foreach src,$(CPP_MODULE_SRC),$(eval $(call cpp_module_pcm,$(src)): $(call cpp_module_import_pcms,$(src))))

.SECONDARY: $(CPP_MODULE_PCM)

$(BUILD_DIR)/%.module.o : $(BUILD_DIR)/%.pcm
	mkdir -p $(@D)
	$(CXX) $(CPP_MODULE_OBJ_FLAGS) -c $< -o $@

# Include all .d files
-include $(DEP)

#------------------------------------------------------------------------
# Systemc build phony targets
#------------------------------------------------------------------------

.PHONY : all clean
.DEFAULT_GOAL = all

all: gen
ifdef VL_DUT
	$(MAKE) -C $(REPO_ROOT)/verif/vl_wrap vlwrap
endif
	$(MAKE) $(BIN_DIR)/$(BIN)

clean::
	$(RM) -r $(BIN_DIR)
	$(RM) -rf simx.*
	@test -d $(REPO_ROOT)/verif/vl_wrap && $(MAKE) -C $(REPO_ROOT)/verif/vl_wrap clean || true

help::
	@echo "  all     	- Build the project binary"
	@echo "  compdb  	- Generate compile_commands.json for clangd"
	@echo "  clangd  	- Generate .clangd configuration for IDE"
	@echo "Makefile Runtime Variables:"
	@echo "  VL_DUT=1	- Build verilator wrapper for the DUT instances"

#------------------------------------------------------------------------
# Generate compile_commands.json for clangd/OpenCode
#------------------------------------------------------------------------

.PHONY: compdb
compdb:
	@mkdir -p $(GEN_BUILD_DIR)
	@$(MAKE) -n -B all > $(GEN_BUILD_DIR)/compdb.model.make-n.txt
	@$(MAKE) -n -B all VL_DUT=1 > $(GEN_BUILD_DIR)/compdb.vl.make-n.txt
	@python3 $(A2C_ROOT)/pysrc/gen_compile_commands.py \
		$(GEN_BUILD_DIR)/compdb.model.make-n.txt \
		$(GEN_BUILD_DIR)/compdb.vl.make-n.txt \
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
