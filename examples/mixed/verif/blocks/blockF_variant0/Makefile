PROJECT_NAME = mixed

REPO_ROOT = $(shell git rev-parse --show-toplevel)
PROJECT_ROOT = $(REPO_ROOT)/examples/$(PROJECT_NAME)

include $(REPO_ROOT)/examples/include/shared.mk

.PHONY : lib all clean

ifndef VERILATOR_ROOT
VERILATOR_ROOT = /usr/local/share/verilator
endif

COMMON_DIR = $(PROJECT_ROOT)/includes
MODEL_DIR = $(PROJECT_ROOT)/model
BUILDER_SC_COMMON = $(REPO_ROOT)/common/systemc

CXX = clang++
INCLUDES = -I$(PROJECT_ROOT)/verif/vl_wrap -I$(PROJECT_ROOT)/verif/vl_wrap/blocks -I$(PROJECT_ROOT)/verif/vl_wrap/obj_dir -I$(COMMON_DIR) -I$(MODEL_DIR) -I$(VERILATOR_ROOT)/include -I$(VERILATOR_ROOT)/include/vltstd -I$(BUILDER_SC_COMMON)

CXXFLAGS = -c -std=c++17 -MMD -DVERILATOR -DVM_TRACE_VCD -DVERIF_TB $(INCLUDES)
LDFLAGS = -L$(PROJECT_ROOT)/verif/vl_wrap -L$(SYSTEMC_LIBDIR) -lvl_s_wrap -lsystemc -latomic -lpthread -ldl -lfmt -L$(LD_BOOST) -lboost_system -lboost_program_options

BUILD_DIR = ./build

CPP_SRCS = src/sc_main.cpp 
CPP_SRCS += $(wildcard $(BUILDER_SC_COMMON)/*.cpp)
CPP_SRCS += $(wildcard $(MODEL_DIR)/*Includes.cpp)
-include build/src/sc_main.d

# All .o files go to build dir.
OBJ_FILES = $(CPP_SRCS:%.cpp=$(BUILD_DIR)/%.o)

$(BUILD_DIR)/%.o: %.cpp
	mkdir -p $(@D)
	$(CXX) $(CXXFLAGS) $< -o $@

$(BUILD_DIR)/simx : $(OBJ_FILES)
	$(CXX) -std=c++17 $(OBJ_FILES) $(LDFLAGS) -o $@

lib:
	$(MAKE) -C $(PROJECT_ROOT)/verif/vl_wrap libvl_s_wrap.a

all: lib
	$(MAKE) $(BUILD_DIR)/simx

run:
	$(BUILD_DIR)/simx

clean:
	rm -rf build *.vcd
	
clean_all : clean
	$(MAKE) -C $(PROJECT_ROOT)/verif/vl_wrap clean
