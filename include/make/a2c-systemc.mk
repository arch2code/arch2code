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

CXX_FLAGS = -m64 -std=$(C_STD_VER) -g -Wfatal-errors -Wall -Wextra -Wpedantic -Wshadow -Wno-unused-variable -Wno-unused-parameter -pthread -DBOOST_STACKTRACE_LINK -DSC_CPLUSPLUS=201703L
LD_FLAGS = -lboost_system -lboost_program_options -lboost_stacktrace_basic -L$(LD_BOOST) -L$(SYSTEMC_LIBDIR) -ldl -lrt -lsystemc
CPP_INCLUDES = -I$(BOOST_INCLUDE) -I$(SYSTEMC_INCLUDE) -I/usr/local/include

A2C_SRC_DIRS = $(A2C_ROOT)/common/systemc $(A2C_ROOT)/common/scmain
PRJ_SRC_DIRS = $(call find_cpp_source_directories, $(REPO_ROOT)/base $(REPO_ROOT)/model $(REPO_ROOT)/fw $(REPO_ROOT)/tb)

ifndef USE_GCC
CXX_FLAGS += -fstandalone-debug
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

ifdef VL_DUT
CPP_SRC += $(REPO_ROOT)/verif/vl_wrap/vl_wrap.cpp
CPP_INCLUDES += -I$(REPO_ROOT)/verif/vl_wrap -I$(VERILATOR_ROOT)/include -I$(VERILATOR_ROOT)/include/vltstd -I$(REPO_ROOT)/verif/vl_wrap/obj_dir
endif

# All include directories.
CPP_INCLUDES +=  $(foreach dir, $(A2C_SRC_DIRS), -I$(dir))
CPP_INCLUDES +=  $(foreach dir, $(PRJ_SRC_DIRS), -I$(dir))

# Put all auto generated stuff to this build dir.
BIN = run
BIN_DIR = $(PROJECT_RUNDIR)/build
BUILD_DIR = $(BIN_DIR)/$(PROJECTNAME).build

# Add to compiler dependencies
CXX_FLAGS += $(CPP_INCLUDES)

ifdef VL_DUT
CXX_FLAGS += -DVERILATOR
LD_FLAGS += -L$(REPO_ROOT)/verif/vl_wrap -l$(PROJECTNAME)vl_s_wrap -latomic
# https://github.com/verilator/verilator/issues/5672
CXX_FLAGS += -Wno-sign-compare
endif

#------------------------------------------------------------------------
# Systemc build file based targets
#------------------------------------------------------------------------

# main receipe to build the binary

# All .o files go to build dir.
OBJ = $(CPP_SRC:%.cpp=$(BUILD_DIR)/%.o)
# Gcc/Clang will create these .d files containing dependencies.
DEP = $(OBJ:%.o=%.d)

# Actual target of the binary - depends on all .o files.
$(BIN_DIR)/$(BIN) : $(OBJ)
    # Create build directories - same structure as sources.
	mkdir -p $(@D)
    # Just link all the object files.
	$(CXX) $(CXX_FLAGS) -o $@ $^ $(LD_FLAGS)

# Rule to compile files in O3_CPP_SRC to add -o3 optimization
$(O3_CPP_SRC:%.cpp=$(BUILD_DIR)/%.o): $(BUILD_DIR)/%.o: %.cpp
	mkdir -p $(@D)
	$(CXX) -O3 $(CXX_FLAGS) -MMD -c $< -o $@

# Rule to compile all other .cpp files
# The -MMD flags additionaly creates a .d file with the same name as the .o file.
$(BUILD_DIR)/%.o : %.cpp $(GEN_DB_DEPS)
	mkdir -p $(@D)
	$(CXX) $(CXX_FLAGS) -MMD -c $< -o $@

# Include all .d files
-include $(DEP)

#------------------------------------------------------------------------
# Systemc build phony targets
#------------------------------------------------------------------------

.PHONY : all clean
.DEFAULT_GOAL = all

all: gen
ifdef VL_DUT
	$(MAKE) -C $(REPO_ROOT)/verif/vl_wrap lib$(PROJECTNAME)vl_s_wrap.a
endif
	$(MAKE) $(BIN_DIR)/$(BIN)

clean::
	$(RM) -r $(BIN_DIR)
	$(RM) -rf simx.*
	$(MAKE) -C $(REPO_ROOT)/verif/vl_wrap clean

help::
	@echo "  all     	- Build the project binary"
	@echo "Makefile Runtime Variables:"
	@echo "  VL_DUT=1	- Build verilator wrapper for the DUT instances"
