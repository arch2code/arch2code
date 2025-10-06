


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
CXX_FLAGS = -std=c++23 -g -Wfatal-errors -Wall -Wextra -Wpedantic -Wshadow -Wno-unused-variable -Wno-unused-parameter -DSC_CPLUSPLUS=201703L
LD_FLAGS = -lboost_system -lboost_program_options -L$(LD_BOOST) -L$(SYSTEMC_LIBDIR) -lsystemc
INCLUDE = -I$(BOOST_INCLUDE) -I$(SYSTEMC_INCLUDE) -I/usr/local/include

# Put all auto generated stuff to this build dir.
BUILD_DIR = ./build

# List of all .cpp source files.
CPP = $(wildcard *.cpp)
HPP = $(wildcard *.h)

.DEFAULT_GOAL = common
.PHONY = common

# All .o files go to build dir.
OBJ = $(CPP:%.cpp=$(BUILD_DIR)/%.o)
# Gcc/Clang will create these .d files containing dependencies.
DEP = $(OBJ:%.o=%.d)

# Actual target of the binary - depends on all .o files.
common : $(OBJ)
    # Create build directories - same structure as sources.
	mkdir -p $(@D)

# Include all .d files
-include $(DEP)

# Build target for every single object file.
# The potential dependency on header files is covered
# by calling `-include $(DEP)`.
$(BUILD_DIR)/%.o : %.cpp
	mkdir -p $(@D)
    # The -MMD flags additionaly creates a .d file with
    # the same name as the .o file.
	$(CXX) $(CXX_FLAGS) -MMD -c $< -o $@ $(INCLUDE)

.PHONY : clean
clean :
    # This should remove all generated files.
	$(RM) -r $(BUILD_DIR)
