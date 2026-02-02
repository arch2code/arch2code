# Project agnostic Makefile for A2C (Arch2Code) based projects
# This file is included by project specific Makefiles to provide common functionality.

#------------------------------------------------------------------------
# Check mandatory variables are set when including this makefile
#------------------------------------------------------------------------

ifndef REPO_ROOT
$(error REPO_ROOT is not set - please set to the root of your repository)
endif
ifndef PROJECTNAME
$(error PROJECTNAME is not set - please set to the name of your project)
endif
ifndef TB_TOP_MODULE
$(error TB_TOP_MODULE is not set - please set to the name of your testbench top module)
endif
ifndef HDL_TOP_MODULE
$(error HDL_TOP_MODULE is not set - please set to the name of your HDL top module)
endif

#------------------------------------------------------------------------
# Helper macro functions to find source files in list of root directories
#------------------------------------------------------------------------

define find_cpp_sources
	$(shell for dir in $(1); do \
		if [ -d "$$dir" ]; then \
			find -L $$dir -type f \( -name '*.cpp' -or -name '*.h' \) ; \
		fi \
	done)
endef

define find_sv_sources
	$(shell for dir in $(1); do \
		if [ -d "$$dir" ]; then \
			find -L $$dir -type f \( -name '*.sv' -or -name '*.svh' \) ; \
		fi \
	done)
endef

define find_gen_cpp_sources
	$(shell for dir in $(1); do \
		if [ -d "$$dir" ]; then \
			find -L $$dir -type f \( -name '*.cpp' -or -name '*.h' \) -exec grep -l 'GENERATED_CODE_' {} \; ; \
		fi \
	done)
endef

define find_gen_sv_sources
	$(shell for dir in $(1); do \
		if [ -d "$$dir" ]; then \
			find -L $$dir -type f \( -name '*.sv' -or -name '*.svh' \) -exec grep -l 'GENERATED_CODE_' {} \; ; \
		fi \
	done)
endef

define find_cpp_source_directories
	$(shell for dir in $(1); do \
		if [ -d "$$dir" ]; then \
			find -L $$dir -type f \( -name '*.cpp' -or -name '*.h' \) -exec dirname {} \; | sort -u ; \
		fi \
	done)
endef

define find_sv_source_directories
	$(shell for dir in $(1); do \
		if [ -d "$$dir" ]; then \
			find -L $$dir -type f \( -name '*.sv' -or -name '*.svh' \) -exec dirname {} \; | sort -u ; \
		fi \
	done)
endef

#------------------------------------------------------------------------
# Project global variables
#------------------------------------------------------------------------

YAML_FILES = $(shell find $(REPO_ROOT)/arch/yaml/ -type f -name '*.yaml')
A2C_PRJ_YAML = $(REPO_ROOT)/arch/yaml/project.yaml
A2C_SQLDB_FILE = $(REPO_ROOT)/$(PROJECTNAME).db
A2C_SQLDB_DOTFILE = $(REPO_ROOT)/.$(PROJECTNAME).db

PROJECT_RUNDIR = $(REPO_ROOT)/rundir

GEN_BUILD_DIR = $(REPO_ROOT)/.gen

SC_GEN_FILES =  $(call find_gen_cpp_sources, $(REPO_ROOT)/base/ $(REPO_ROOT)/model/ $(REPO_ROOT)/tb/ $(REPO_ROOT)/verif/vl_wrap $(REPO_ROOT)/fw/)
SC_GEN_DOT_FILES = $(SC_GEN_FILES:%=$(GEN_BUILD_DIR)/%.scgen)

SV_GEN_FILES =  $(call find_gen_sv_sources, $(REPO_ROOT)/rtl/ $(REPO_ROOT)/verif/vl_wrap) $(REPO_ROOT)/rtl/rtl.f
SV_GEN_DOT_FILES = $(SV_GEN_FILES:%=$(GEN_BUILD_DIR)/%.svgen)

ifndef SKIP_GEN
GEN_DEPS = $(SC_GEN_DOT_FILES) $(SV_GEN_DOT_FILES)
else
$(warning "Forced skipping generation step (SKIP_GEN=1)")
endif

# C++ compilation global variables
ifndef USE_GCC
  CXX=clang++
  C_STD_VER=c++23
else
  CXX=g++
  C_STD_VER=c++23
endif

#------------------------------------------------------------------------
# Project global file based targets
#------------------------------------------------------------------------

$(A2C_SQLDB_FILE): $(YAML_FILES)
	$(A2C_ROOT)/arch2code.py -y $(A2C_PRJ_YAML) --db $(A2C_SQLDB_FILE)
	touch $(A2C_SQLDB_DOTFILE)

$(GEN_BUILD_DIR)/%.scgen: % $(A2C_SQLDB_FILE)
	$(A2C_ROOT)/arch2code.py --db $(A2C_SQLDB_FILE) -r --systemc --file $<
	@mkdir -p $(@D) && touch $@

$(GEN_BUILD_DIR)/%.svgen: % $(A2C_SQLDB_FILE)
	$(A2C_ROOT)/arch2code.py --db $(A2C_SQLDB_FILE) -r --systemVerilog --file $<
	@mkdir -p $(@D) && touch $@

#------------------------------------------------------------------------
# Project global phony targets
#------------------------------------------------------------------------

.PHONY: db gen newmodule clean

db : $(A2C_SQLDB_FILE)


gen: $(GEN_DEPS)

newmodule: $(A2C_SQLDB_FILE)
	$(A2C_ROOT)/arch2code.py --db $(A2C_SQLDB_FILE) -r --newmodule
	touch $(A2C_SQLDB_FILE)

clean::
	rm -rf $(GEN_BUILD_DIR)
	rm -f $(A2C_SQLDB_FILE) $(A2C_SQLDB_DOTFILE)


help::
	@echo "Usage: make [target] [vars]"
	@echo "Available targets:"
	@echo "  db       	- Generate or update the project database"
	@echo "  gen      	- Generate SystemC and SystemVerilog files from the project database"
	@echo "  newmodule	- Create a new module in the project database"
	@echo "  clean    	- Clean generated files and project database"
	@echo "  help     	- Show this help message"

#------------------------------------------------------------------------
# Include AI agent setup targets
#------------------------------------------------------------------------
include $(A2C_ROOT)/include/make/a2c-agents.mk
