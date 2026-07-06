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
			find -L $$dir -type f \( -name '*.cpp' -or -name '*.h' -or -name '*.cppm' \) ; \
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
			find -L $$dir -type f \( -name '*.cpp' -or -name '*.h' -or -name '*.cppm' \) -exec grep -l 'GENERATED_CODE_' {} \; ; \
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

#------------------------------------------------------------------------
# Project global variables
#------------------------------------------------------------------------

# Project file is a build *input* (it builds the database that emits the
# manifest), so it cannot come from the manifest. Default to the functional
# location; a hierarchical project's shared.mk re-points it ($prj/yaml/...).
A2C_PRJ_YAML ?= $(REPO_ROOT)/arch/yaml/project.yaml
A2C_SQLDB_FILE = $(REPO_ROOT)/$(PROJECTNAME).db
A2C_SQLDB_DOTFILE = $(REPO_ROOT)/.$(PROJECTNAME).db

PROJECT_RUNDIR = $(REPO_ROOT)/rundir

GEN_BUILD_DIR = $(REPO_ROOT)/.gen

# Build directory/file set is derived by projectCreate (buildManifest) and
# emitted as a side effect of the database build (.gen/build.mk: source/include
# dirs, the verilated entry, the YAML dependency closure). Including it replaces
# the fixed-functional-root globs below, so discovery follows the project's
# layout instead of assuming $root/base, $root/model, ... The database build
# regenerates it, so it is declared as a target depending on the db: on a clean
# tree `make` builds the db (emitting the manifest) and re-execs with the dir
# lists populated; the established `make db` then `make gen` flow has it present
# by gen time. The leading dash keeps the very first parse (no manifest yet) quiet.
$(GEN_BUILD_DIR)/build.mk: $(A2C_SQLDB_FILE) ;
-include $(GEN_BUILD_DIR)/build.mk

# YAML dependency list (db rebuild trigger) is the parsed include-tree closure
# the manifest records; empty before the first db build, when the db is built
# unconditionally anyway.
YAML_FILES = $(A2C_YAML_FILES)

# Generated source discovery is scoped to the manifest's dirs (a per-dir search
# for files carrying GENERATED markers), not fixed functional roots.
SC_GEN_FILES =  $(call find_gen_cpp_sources, $(A2C_SC_SRC_DIRS) $(A2C_VL_WRAP_DIRS))
SC_GEN_DOT_FILES = $(SC_GEN_FILES:%=$(GEN_BUILD_DIR)/%.scgen)

SV_GEN_FILES =  $(call find_gen_sv_sources, $(A2C_SV_SRC_DIRS) $(A2C_VL_WRAP_DIRS)) $(wildcard $(REPO_ROOT)/rtl/rtl.f)
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

.PHONY: db gen newmodule migrate migrate-hierarchical clean

db : $(A2C_SQLDB_FILE)


# Migrate the project's user YAML to the current authoring format and stamp the
# yamlFormat sentinel. Standalone: it reads and rewrites YAML as text and does
# not build the database, so it runs on a project the yamlFormat gate rejects.
migrate:
	$(A2C_ROOT)/migrateYaml.py --write $(A2C_PRJ_YAML)


# Opt-in functional -> hierarchical layout migration. Separate from `migrate`:
# it relocates files (the unconditional phases edit content in place) and
# presupposes the project is already yamlFormat: 2, so it runs only after
# `migrate`. See plan-decomp-functional-layout.md "Phase 4 - L4".
migrate-hierarchical:
	$(A2C_ROOT)/migrateYaml.py --to-hierarchical --write $(A2C_PRJ_YAML)


gen: $(GEN_DEPS)

newmodule: $(A2C_SQLDB_FILE)
	$(A2C_ROOT)/arch2code.py --db $(A2C_SQLDB_FILE) -r --newmodule
	touch $(A2C_SQLDB_FILE)
	@# Refresh clangd compilation database after adding sources.
	@$(MAKE) -C $(PROJECT_RUNDIR) compdb >/dev/null

clean::
	rm -rf $(GEN_BUILD_DIR)
	rm -f $(A2C_SQLDB_FILE) $(A2C_SQLDB_DOTFILE)


help::
	@echo "Usage: make [target] [vars]"
	@echo "Available targets:"
	@echo "  db       	- Generate or update the project database"
	@echo "  gen      	- Generate SystemC and SystemVerilog files from the project database"
	@echo "  newmodule	- Create a new module in the project database"
	@echo "  migrate  	- Migrate the project YAML to the current authoring format"
	@echo "  clean    	- Clean generated files and project database"
	@echo "  help     	- Show this help message"

#------------------------------------------------------------------------
# Include AI agent setup targets
#------------------------------------------------------------------------
include $(A2C_ROOT)/include/make/a2c-agents.mk
