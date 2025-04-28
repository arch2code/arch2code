REPO_ROOT = $(shell git rev-parse --show-toplevel)

PROJECTNAME = axiDemo
DB_FILE = ../$(PROJECTNAME).db
DOT_DB_FILE = ../.$(PROJECTNAME).db

$(DOT_DB_FILE):
	make -C ../arch

db: $(DOT_DB_FILE) 

ifndef SYSTEMC_INCLUDE
$(error SYSTEMC_INCLUDE is not set - please set to systemc-2.3.4 install directory)
endif
ifndef SYSTEMC_LIBDIR
$(error SYSTEMC_LIBDIR is not set - please set to systemc-2.3.4 install directory)
endif
ifndef BOOST_INCLUDE
$(error BOOST_INCLUDE is not set - please set to boost directory containing .h files)
endif
ifndef LD_BOOST
$(error LD_BOOST is not set - please set to boost library (.so) path)
endif

CXX = clang++
CXX_FLAGS = -std=c++17 -g -Wfatal-errors -Wall -Wextra -Wpedantic -Wshadow -Wno-unused-variable -Wno-unused-parameter
LD_FLAGS = -lboost_system -lboost_program_options -L$(LD_BOOST) -L$(SYSTEMC_LIBDIR) -lsystemc -lfmt
INCLUDE = -I$(BOOST_INCLUDE) -I$(SYSTEMC_INCLUDE) -I$(REPO_ROOT)/common/systemc -I../includes -I. -I/usr/local/include
# Final binary
BIN = $(PROJECTNAME)
# Put all auto generated stuff to this build dir.
BUILD_DIR = ./build

# List of all .cpp source files.
CPP = $(wildcard *.cpp) $(wildcard ../includes/*.cpp )
HPP = $(wildcard *.h) $(wildcard ../includes/*.h )

.DEFAULT_GOAL = $(BUILD_DIR)/$(BIN)
.PHONY : gen db common run

GEN_FILES = $(shell find . ../includes \( -name '*.cpp' -or -name '*.h' \) -exec grep -E -l 'GENERATED_CODE_BEGIN' {} +)
#$(info  Genfiles $(GEN_FILES) )
# All .o files go to build dir.
OBJ = $(CPP:%.cpp=$(BUILD_DIR)/%.o)
COMMON_CPP = $(wildcard $(REPO_ROOT)/common/systemc/*.cpp)
#$(info  COMMON_CPP $(COMMON_CPP) )
COMMON_OBJ = $(patsubst $(REPO_ROOT)/common/systemc/%.cpp,$(REPO_ROOT)/common/systemc/build/%.o,$(COMMON_CPP))
#$(info  COMMON_OBJ $(COMMON_OBJ) )
# Gcc/Clang will create these .d files containing dependencies.
DEP = $(OBJ:%.o=%.d)

# Default target named after the binary.
$(BIN) : $(BUILD_DIR)/$(BIN)

# Actual target of the binary - depends on all .o files.
$(BUILD_DIR)/$(BIN) : $(OBJ) $(COMMON_OBJ)
    # Create build directories - same structure as sources.
	mkdir -p $(@D)
    # Just link all the object files.
	$(CXX) $(CXX_FLAGS) $(LD_FLAGS) $^ -o $@

# Include all .d files
-include $(DEP)

$(GEN_FILES) : $(DOT_DB_FILE) mdlBlockList.yaml
	$(REPO_ROOT)/arch2code.py --readonly --db $(DB_FILE) --systemc --instances mdlBlockList.yaml --file $@

gen: $(GEN_FILES)

$(COMMON_OBJ) : common

common:
	make -C $(REPO_ROOT)/common/systemc

all: $(BUILD_DIR)/$(BIN)

run : all
	$(BUILD_DIR)/$(BIN)

# Build target for every single object file.
# The potential dependency on header files is covered
# by calling `-include $(DEP)`.
$(BUILD_DIR)/%.o : %.cpp $(DOT_DB_FILE) $(GEN_FILES)
	mkdir -p $(@D)
    # The -MMD flags additionaly creates a .d file with
    # the same name as the .o file.
	$(CXX) $(CXX_FLAGS) -MMD -c $< -o $@ $(INCLUDE)

.PHONY : clean
clean :
    # This should remove all generated files.
	$(RM) -r $(BUILD_DIR)
	$(RM) -f $(DB_FILE) $(DOT_DB_FILE)
