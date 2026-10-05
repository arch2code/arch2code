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

# A site EXTRA_LD_FLAGS arrives through the environment, and make exports it to
# every sub-make with the project's `+=` already appended. Each sub-make
# re-reads that `+=`, so it restarts from the site value the outermost make
# captured here, before the project Makefile appends. Only a sub-make
# (MAKELEVEL above 0) restores, so a marker left in the user's shell is ignored.
ifneq ($(and $(filter-out 0,$(MAKELEVEL)),$(filter environment,$(origin A2C_SITE_EXTRA_LD_FLAGS))),)
EXTRA_LD_FLAGS = $(A2C_SITE_EXTRA_LD_FLAGS)
else
export A2C_SITE_EXTRA_LD_FLAGS := $(value EXTRA_LD_FLAGS)
endif

PROJECT_RUNDIR = $(REPO_ROOT)/rundir

# Binary/object/dependency tree of the rundir build. Defined here rather than in
# a2c-systemc.mk so `clean` from the project root removes it too: dependency
# files left behind name sources that a later release may have deleted, and the
# next build then fails with "No rule to make target".
BIN_DIR = $(PROJECT_RUNDIR)/build

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
# the manifest records. A manifest written for another project root (a copied
# or moved tree), or naming YAML that no longer exists (a moved builder, a
# deleted include), is stale: its YAML paths are dropped and the db rebuilds.
# The manifest is rewritten only by a db build that reaches the manifest step,
# so a failed rebuild leaves it stale and the next make forces again. Only the
# first parse forces, so a restart after the rebuild cannot loop.
A2C_MANIFEST_OTHER_ROOT := $(filter-out $(realpath $(A2C_MANIFEST_REPO_ROOT)),$(realpath $(REPO_ROOT)))
A2C_MANIFEST_MISSING_YAML := $(filter-out $(wildcard $(A2C_YAML_FILES)),$(A2C_YAML_FILES))
ifeq ($(A2C_MANIFEST_OTHER_ROOT)$(A2C_MANIFEST_MISSING_YAML),)
YAML_FILES = $(A2C_YAML_FILES)
else
YAML_FILES =
ifeq ($(MAKE_RESTARTS),)
$(A2C_SQLDB_FILE): a2c-manifest-stale
.PHONY: a2c-manifest-stale
a2c-manifest-stale: ;
endif
endif

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

# Python catalogs share the SystemC gen path (%.scgen) but are not C++ hosts.
# The PY recipe passes --python so the generator chooses the # delimiter.
PY_GEN_FILES = $(wildcard $(A2C_PY_GEN_FILES))
PY_GEN_DOT_FILES = $(PY_GEN_FILES:%=$(GEN_BUILD_DIR)/%.scgen)

SV_GEN_FILES =  $(wildcard $(A2C_SV_GEN_FILES)) $(wildcard $(A2C_RTL_DOT_F)) $(wildcard $(EXTRA_SV_GEN_FILES))
SV_GEN_DOT_FILES = $(SV_GEN_FILES:%=$(GEN_BUILD_DIR)/%.svgen)

ifndef SKIP_GEN
GEN_DEPS = $(SC_GEN_DOT_FILES) $(SV_GEN_DOT_FILES) $(PY_GEN_DOT_FILES)
else
$(warning "Forced skipping generation step (SKIP_GEN=1)")
endif

# C++ compilation global variables. A site names its Clang through A2C_CLANG, a
# single compiler path with no launcher word; an exported CXX is ignored, so a
# toolchain environment that exports CXX=g++ cannot switch compilers unseen.
ifndef USE_GCC
  CXX = $(or $(A2C_CLANG),clang++)
  C_STD_VER=c++23
else
  CXX=g++
  C_STD_VER=c++23
endif

#------------------------------------------------------------------------
# Project global file based targets
#------------------------------------------------------------------------

# A failed recipe leaves no target file behind. arch2code writes the database as
# it runs, so a partial one would otherwise look newer than its YAML and let
# later builds skip the db stage and generate against it. Generation targets its
# .gen stamp, so a user source file is never a target here.
.DELETE_ON_ERROR:

# Builder stamp: every generator input of the builder (templates, generator
# modules, config, arch2code.py, and pro's templates and config when present)
# with its mtime. The parse rewrites the stamp only when that listing changes,
# so an added, removed or edited builder file regenerates the project and an
# unchanged builder leaves it alone.
A2C_BUILDER_STAMP = $(GEN_BUILD_DIR)/builder.stamp
A2C_BUILDER_INPUTS = find -L $(A2C_ROOT)/templates $(A2C_ROOT)/pysrc $(wildcard $(A2C_ROOT)/config/*.yaml $(A2C_ROOT)/config/*.py $(A2C_ROOT)/arch2code.py $(A2C_ROOT)/pro/templates $(A2C_ROOT)/pro/config) -name __pycache__ -prune -o -type f -printf '%p %T@\n' | LC_ALL=C sort
$(shell mkdir -p $(GEN_BUILD_DIR); l="$$($(A2C_BUILDER_INPUTS))"; [ "$$(cat $(A2C_BUILDER_STAMP) 2>/dev/null)" = "$$l" ] || { printf '%s\n' "$$l" > $(A2C_BUILDER_STAMP).$$$$ && mv -f $(A2C_BUILDER_STAMP).$$$$ $(A2C_BUILDER_STAMP); })

$(A2C_SQLDB_FILE): $(A2C_BUILDER_STAMP)
$(A2C_SQLDB_FILE): $(YAML_FILES)
	@# arch2code writes the manifest under dirs: root. Removing the old one first
	@# means a missing manifest afterwards shows that dirs: root and REPO_ROOT
	@# name different directories.
	rm -f $(GEN_BUILD_DIR)/build.mk
	$(A2C_ROOT)/arch2code.py -y $(A2C_PRJ_YAML) --db $(A2C_SQLDB_FILE)
	@[ -f $(GEN_BUILD_DIR)/build.mk ] || echo "warning: $(GEN_BUILD_DIR)/build.mk stays stale: the db build wrote no manifest under REPO_ROOT $(REPO_ROOT). REPO_ROOT and the project's dirs: root in $(A2C_PRJ_YAML) name different directories, so every make rebuilds the db." >&2
	touch $(A2C_SQLDB_DOTFILE)

$(SC_GEN_DOT_FILES): $(GEN_BUILD_DIR)/%.scgen: % $(A2C_SQLDB_FILE)
	$(A2C_ROOT)/arch2code.py --db $(A2C_SQLDB_FILE) -r --systemc --file $<
	@mkdir -p $(@D) && touch $@

$(PY_GEN_DOT_FILES): $(GEN_BUILD_DIR)/%.scgen: % $(A2C_SQLDB_FILE)
	$(A2C_ROOT)/arch2code.py --db $(A2C_SQLDB_FILE) -r --systemc --file $< --python
	@mkdir -p $(@D) && touch $@

$(GEN_BUILD_DIR)/%.svgen: % $(A2C_SQLDB_FILE)
	$(A2C_ROOT)/arch2code.py --db $(A2C_SQLDB_FILE) -r --systemVerilog --file $<
	@mkdir -p $(@D) && touch $@

#------------------------------------------------------------------------
# Project global phony targets
#------------------------------------------------------------------------

.PHONY: db gen newmodule migrate migrate-hierarchical clean

db : $(A2C_SQLDB_FILE)


# Migrate a project to the current authoring format. The stamp step fails
# while yaml-stage TODOs remain, so nothing below runs on an unstamped project.
# Ordering: the sweep runs before newmodule so stale markers cannot feed the
# scaffold; newmodule runs before gen because gen only fills generated regions
# of files that already exist; --port-tb runs before gen so its region edits
# are in place when gen renders; --port runs after gen because it transplants
# user code into gen-filled .cppm files.
# Exit 1 from --sweep, --port-tb or --port is pending hand work and does not
# halt, so the tree still regenerates. The first sweep's exit 1 is not the
# verdict, because the porters below resolve the legacy pairs it reports.
# Exit 2 halts at once. --sweep returns it when the filename-prefix move is
# blocked, or when opening the database, the move or its blocked report raises,
# since newmodule would delete a file left unmoved. --port-tb returns it when
# the Config.cpp restructure is refused or raises, since gen would abort on
# that file. Exit 3 from --sweep means a phase raised. The final read-only
# sweep cannot see a write that failed, so the recipe exits 1 for it. The
# recipe also exits 1 when a porter or the final sweep reports a TODO.
migrate:
	$(A2C_ROOT)/migrateYaml.py --write $(A2C_PRJ_YAML)
	$(MAKE) db
	$(A2C_ROOT)/migrateYaml.py --sweep --write --db $(A2C_SQLDB_FILE); src=$$?; \
	case $$src in 0|1) rc=0 ;; 3) rc=1 ;; *) exit $$src ;; esac; \
	if [ $$src -ne 0 ]; then echo "Later phases of this run may resolve TODO items reported above." \
	  "A TODO_PHASE_FAILED item above needs a fix and a re-run."; fi; \
	$(MAKE) newmodule && \
	{ $(A2C_ROOT)/migrateYaml.py --port-tb --write --db $(A2C_SQLDB_FILE); trc=$$?; \
	  if [ $$trc -eq 1 ]; then rc=1; elif [ $$trc -ne 0 ]; then exit $$trc; fi; } && \
	$(MAKE) gen && \
	{ $(A2C_ROOT)/migrateYaml.py --port --write --db $(A2C_SQLDB_FILE); prc=$$?; \
	  if [ $$prc -eq 1 ]; then rc=1; elif [ $$prc -ne 0 ]; then exit $$prc; fi; } && \
	echo "=== pending after all phases (read-only sweep) ===" && \
	{ $(A2C_ROOT)/migrateYaml.py --sweep --db $(A2C_SQLDB_FILE) || rc=1; } && \
	exit $$rc


# Opt-in functional -> hierarchical layout migration. Separate from `migrate`:
# it relocates files (the unconditional phases edit content in place) and
# presupposes the project is already yamlFormat: 2, so it runs only after
# `migrate`.
migrate-hierarchical:
	$(A2C_ROOT)/migrateYaml.py --to-hierarchical --write $(A2C_PRJ_YAML)


gen: $(GEN_DEPS)

# Creates missing fileMap files, never rewrites an existing one, and deletes
# registrar files the current contract no longer names.
newmodule: $(A2C_SQLDB_FILE)
	$(A2C_ROOT)/arch2code.py --db $(A2C_SQLDB_FILE) -r --newmodule
	touch $(A2C_SQLDB_FILE)
	@# The compdb parse scans .cppm scaffolds gen has not filled yet and fails;
	@# keep it non-fatal so newmodule and migrate proceed.
	@$(MAKE) -C $(PROJECT_RUNDIR) compdb >/dev/null 2>&1 || true

clean::
	rm -rf $(GEN_BUILD_DIR) $(BIN_DIR)
	rm -f $(A2C_SQLDB_FILE) $(A2C_SQLDB_DOTFILE)


help::
	@echo "Usage: make [target] [vars]"
	@echo "Available targets:"
	@echo "  db       	- Generate or update the project database"
	@echo "  gen      	- Generate SystemC and SystemVerilog files from the project database"
	@echo "  newmodule	- Scaffold missing module files, drop stale registrar and verification-wrapper files"
	@echo "  migrate  	- Migrate to the current authoring format (yaml convert + stamp, db, orphan sweep, gen)"
	@echo "  clean    	- Clean generated files and project database"
	@echo "  help     	- Show this help message"

#------------------------------------------------------------------------
# Include AI agent setup targets
#------------------------------------------------------------------------
include $(A2C_ROOT)/include/make/a2c-agents.mk
