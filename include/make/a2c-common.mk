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

# Generated source set is the manifest's authoritative DB-derived enumeration:
# the files arch2code scaffolds whole through the fileMap. Filtered through
# wildcard so a not-yet-scaffolded intended file (the manifest lists intent; make
# newmodule scaffolds on disk) is not a missing prerequisite - the build stamps
# only files present. EXTRA_S{C,V}_GEN_FILES is the home for user-hosted
# generated-region files: files whose host (name, segment, any namespace wrapper)
# is user-authored while arch2code injects generated sections into it (e.g.
# address headers via the includes template, encoder units via the encoder
# templates). They layer onto the manifest baseline and stamp for regeneration
# alongside it.
SC_GEN_FILES =  $(wildcard $(A2C_SC_GEN_FILES)) $(wildcard $(EXTRA_SC_GEN_FILES))
SC_GEN_DOT_FILES = $(SC_GEN_FILES:%=$(GEN_BUILD_DIR)/%.scgen)

SV_GEN_FILES =  $(wildcard $(A2C_SV_GEN_FILES)) $(wildcard $(A2C_RTL_DOT_F)) $(wildcard $(EXTRA_SV_GEN_FILES))
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

# YAML_FILES (the manifest include-tree closure) is empty before the first db
# build and never lists the project file itself, so name project.yaml as an
# explicit prerequisite: a `migrate` run that stamps the project file (bumping
# its mtime) then rebuilds the db from the stamped YAML rather than reusing a
# stale (or gate-aborted shell) db.
$(A2C_SQLDB_FILE): $(A2C_PRJ_YAML)
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


# One-command migration to the current authoring format. Orchestrates the whole
# pipeline: the text conversions + yamlFormat stamp, then (only once the project
# is stamped/format-2, so the database gate passes) build the DB, sweep the
# generated orphans the legacy fileMap left behind, scaffold the current fileMap's
# new-form producers the legacy generator never emitted, and regenerate.
# The stamp line fails the target on non-zero (yaml-stage manual TODOs remain,
# project unstamped), halting before db/sweep so the user resolves them and re-runs
# the same idempotent `make migrate`. The sweep applies its deletes, but a remaining
# agent-driven port (TODO_PORT) makes it exit non-zero; rather than halt there —
# which would leave the purely-generated blocks deleted but not recreated —
# newmodule + gen ALWAYS run after the sweep to rescaffold them, then the sweep's
# exit code is re-raised so `make migrate` still signals non-zero while ports remain.
# A newmodule/gen failure still halts. newmodule runs AFTER the sweep and BEFORE gen:
# gen only fills generated regions of files that already exist, so newmodule
# (create-only) must scaffold the missing new-form files first, and the orphans must
# be gone before it so stale markers do not feed the scgen step.
# The block-module port (--port) runs LAST, after gen: it transplants each legacy
# .cpp/.h block pair's user code into the now-gen-filled .cppm (the transplant
# target must already carry its generated regions) and deletes the legacy pair. It
# is idempotent (a block already ported is a no-op) and runs inside the && chain so
# a block it flags for a hand port (parameterized, reg-handler, hostile library,
# non-boilerplate slot-0) surfaces as a non-zero exit; otherwise the sweep's rc is
# re-raised, so a first run that ports cleanly still signals non-zero for the
# pending-then-done TODO_PORT and the idempotent re-run goes clean.
migrate:
	$(A2C_ROOT)/migrateYaml.py --write $(A2C_PRJ_YAML)
	$(MAKE) db
	$(A2C_ROOT)/migrateYaml.py --sweep --write --db $(A2C_SQLDB_FILE); rc=$$?; \
	$(MAKE) newmodule && $(MAKE) gen && \
	$(A2C_ROOT)/migrateYaml.py --port --write --db $(A2C_SQLDB_FILE) && exit $$rc


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
	@# Best-effort clangd compile-DB refresh after adding sources. newmodule
	@# scaffolds EMPTY module-interface units (<block>Base.cppm, <ctx>Includes.cppm)
	@# whose `export module` line is emitted only when `make gen` fills them, so the
	@# rundir compdb parse here runs the C++ module scan over not-yet-generated
	@# .cppm and fails by design. It must never abort newmodule (nor the `migrate`
	@# pipeline, which runs newmodule before gen), so keep it non-fatal.
	@$(MAKE) -C $(PROJECT_RUNDIR) compdb >/dev/null 2>&1 || true

clean::
	rm -rf $(GEN_BUILD_DIR)
	rm -f $(A2C_SQLDB_FILE) $(A2C_SQLDB_DOTFILE)


help::
	@echo "Usage: make [target] [vars]"
	@echo "Available targets:"
	@echo "  db       	- Generate or update the project database"
	@echo "  gen      	- Generate SystemC and SystemVerilog files from the project database"
	@echo "  newmodule	- Create a new module in the project database"
	@echo "  migrate  	- Migrate to the current authoring format (yaml convert + stamp, db, orphan sweep, gen)"
	@echo "  clean    	- Clean generated files and project database"
	@echo "  help     	- Show this help message"

#------------------------------------------------------------------------
# Include AI agent setup targets
#------------------------------------------------------------------------
include $(A2C_ROOT)/include/make/a2c-agents.mk
