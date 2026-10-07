ifndef A2C_INCLUDE_MAKE_A2C_AGENTS_MK_INCLUDED
A2C_INCLUDE_MAKE_A2C_AGENTS_MK_INCLUDED := 1

#------------------------------------------------------------------------
# Check mandatory variables are set when including this makefile
#------------------------------------------------------------------------

ifndef REPO_ROOT
$(error REPO_ROOT is not set - please set to the root of your repository)
endif
ifndef A2C_ROOT
$(error A2C_ROOT is not set - please set to the root of your A2C builder)
endif

#------------------------------------------------------------------------
# AI rule source roots; base always, extensions (e.g. pro) append via EXTRA_A2C_RULES_DIRS
#
# Base content sits at $(A2C_ROOT) when running standalone; under pro (which
# nests base and may not symlink every dir) it sits at $(A2C_ROOT)/base. Detect
# pro by its directory rather than relying on the base-dir symlinks.
#------------------------------------------------------------------------
ifneq ($(wildcard $(A2C_ROOT)/pro),)
A2C_BASE_DIR := $(A2C_ROOT)/base
else
A2C_BASE_DIR := $(A2C_ROOT)
endif
A2C_RULES_DIRS := $(A2C_BASE_DIR)/rules $(EXTRA_A2C_RULES_DIRS)
# Base dir expressed relative to REPO_ROOT, so the rules symlink planted in the
# project root stays relative and survives a moved or renamed checkout. Falls
# back to the absolute path when base is not under REPO_ROOT (an example project
# inside the arch2code repo itself), where a relative link is not expressible.
A2C_BASE_REL := $(patsubst $(REPO_ROOT)/%,%,$(A2C_BASE_DIR))

#------------------------------------------------------------------------
# AI Agent Setup Targets
#
#   agents-setup  : Claude Code, Gemini CLI, OpenCode, Cursor IDE and the cross-tool .agents/ dir
#   agents-clean  : Remove what agents-setup deploys
#   cursor-setup  : Alias of agents-setup
#   cursor-clean  : Alias of agents-clean
#   agent-dev-setup : Install Arch2Code builder/base development skills to all platforms
#   agent-dev-clean : Remove Arch2Code builder/base development skills from all platforms
#
# .agents-setup.md5 holds an md5sum line for each deployed file, path relative
# to REPO_ROOT. Setup replaces each deployed file unless its recorded checksum
# shows you edited it. It keeps and names each edited file. A file with no
# checksum line is replaced, except an AGENTS.md that agents-setup did not
# create. Setup and clean leave that one in place, and agents-clean FORCE=1
# removes it. Clean removes the same files and leaves edited ones in place.
#------------------------------------------------------------------------

.PHONY: agents-setup agents-clean agents_setup agents_clean
.PHONY: cursor-setup cursor-clean cursor_setup cursor_clean
.PHONY: agent-dev-setup agent-dev-clean agent_dev_setup agent_dev_clean

# Shell functions for the recipes below. a2c_install SRC REL copies SRC to REL
# and records it, and returns 1 when it keeps REL. a2c_remove REL returns 1
# unless it removed REL. a2c_count DIR NOUN prints how many files a2c_remove
# took from DIR. The lock on REPO_ROOT serializes recipes that share the
# manifest under make -j. Deployed paths contain no whitespace or glob
# characters, which the word-split lists rely on.
define A2C_AGENTS_SH
R="$(REPO_ROOT)"; M="$$R/.agents-setup.md5"; kept=0; gone=""; \
exec 9<"$$R" && flock 9 || exit 1; \
a2c_state() { \
	if [ ! -e "$$R/$$1" ]; then echo missing; \
	elif [ -f "$$M" ] && grep -Fxq -- "$$(cd "$$R" && md5sum -- "$$1")" "$$M"; then echo unmodified; \
	elif [ -f "$$M" ] && cut -c35- "$$M" | grep -Fxq -- "$$1"; then echo modified; \
	else echo untracked; fi; }; \
a2c_keep() { echo "  = Kept $$1 (modified since setup)"; kept=$$((kept + 1)); }; \
a2c_foreign() { [ "$$1" = AGENTS.md ] && echo "  = Kept AGENTS.md (not created by agents-setup)"; }; \
a2c_record() { \
	[ -f "$$M" ] || [ -n "$$2" ] || return 0; \
	{ if [ -f "$$M" ]; then awk -v p="$$1" 'substr($$0, 35) != p' "$$M"; fi; \
	  if [ -n "$$2" ]; then (cd "$$R" && md5sum -- "$$1"); fi; } > "$$M.tmp" && \
	mv -f "$$M.tmp" "$$M" || { rm -f "$$M.tmp"; echo "  ! Failed to update .agents-setup.md5 for $$1"; exit 1; }; }; \
a2c_install() { \
	case "$$(a2c_state "$$2")" in \
	modified) a2c_keep "$$2"; return 1;; \
	untracked) if a2c_foreign "$$2"; then return 1; fi;; \
	esac; \
	mkdir -p "$$(dirname "$$R/$$2")" && cp -- "$$1" "$$R/$$2.a2c-tmp" && mv -f -- "$$R/$$2.a2c-tmp" "$$R/$$2" || \
	{ rm -f -- "$$R/$$2.a2c-tmp"; echo "  ! Failed to write $$2"; exit 1; }; \
	a2c_record "$$2" add; }; \
a2c_remove() { \
	case "$$(a2c_state "$$1")" in \
	missing) a2c_record "$$1"; return 1;; \
	modified) a2c_keep "$$1"; return 1;; \
	untracked) if a2c_foreign "$$1"; then return 1; fi;; \
	esac; \
	rm -f -- "$$R/$$1" || { echo "  ! Failed to remove $$1"; exit 1; }; \
	gone="$$gone $$1"; \
	a2c_record "$$1"; }; \
a2c_count() { \
	n=0; for g in $$gone; do case "$$g" in "$$1"/*) n=$$((n + 1));; esac; done; \
	if [ $$n = 1 ]; then echo "  - Removed 1 $$2 file from $$1/"; \
	elif [ $$n -gt 1 ]; then echo "  - Removed $$n $$2 files from $$1/"; fi; }; \
a2c_rmdir() { if [ -d "$$R/$$1" ] && [ -z "$$(ls -A "$$R/$$1")" ]; then rmdir "$$R/$$1" && echo "  - Removed empty $$1 directory"; fi; }; \
a2c_setup_note() { \
	if [ $$kept -gt 0 ]; then \
		echo "  ! Kept $$kept file(s) listed above. To replace them with the shipped version, delete them, then run make $$1 and make $$2"; \
	fi; }; \
a2c_clean_note() { \
	if [ -f "$$M" ] && [ ! -s "$$M" ]; then rm -f "$$M" && echo "  - Removed .agents-setup.md5"; fi; \
	if [ $$kept -gt 0 ]; then \
		echo "  ! Left $$kept file(s) listed above in place. To finish the clean, delete them and rerun make $$1"; \
	fi; }
endef

#------------------------------------------------------------------------
# agents-setup: Claude Code / Gemini CLI / OpenCode / Cursor IDE / generic agents
#------------------------------------------------------------------------
agents-setup agents_setup:
	@$(A2C_AGENTS_SH); \
	echo "Setting up AI agent rules (Claude Code, Gemini CLI, OpenCode, Cursor IDE)..."; \
	trap 'rm -f "$$R/.AGENTS.md.new" "$$R/.cursorrules.new"' EXIT; \
	new="$$R/.AGENTS.md.new"; \
	if ! ( cp "$(A2C_BASE_DIR)/AGENTS.md.template" "$$new" || exit 1; \
	     for root in $(A2C_RULES_DIRS); do \
	       frag="$$(dirname "$$root")/AGENTS.append.md"; \
	       if [ -f "$$frag" ]; then \
	         { printf '\n' && cat "$$frag"; } >> "$$new" || exit 1; \
	         echo "  + Appended skill routing from $$frag"; \
	       fi; \
	     done ); then \
		echo "  ! Failed to write AGENTS.md"; \
		exit 1; \
	fi; \
	if a2c_install "$$new" AGENTS.md; then echo "  + Wrote AGENTS.md from template"; fi; \
	if [ ! -L "$$R/CLAUDE.md" ] && [ ! -e "$$R/CLAUDE.md" ]; then \
		ln -s AGENTS.md "$$R/CLAUDE.md" || exit 1; \
		echo "  + Created symlink: CLAUDE.md -> AGENTS.md"; \
	else \
		echo "  = CLAUDE.md already exists"; \
	fi; \
	if [ ! -L "$$R/GEMINI.md" ] && [ ! -e "$$R/GEMINI.md" ]; then \
		ln -s AGENTS.md "$$R/GEMINI.md" || exit 1; \
		echo "  + Created symlink: GEMINI.md -> AGENTS.md"; \
	else \
		echo "  = GEMINI.md already exists"; \
	fi; \
	if [ ! -L "$$R/ARCH2CODE_AI_RULES.md" ] && [ ! -e "$$R/ARCH2CODE_AI_RULES.md" ]; then \
		ln -s $(A2C_BASE_REL)/ARCH2CODE_AI_RULES.md "$$R/ARCH2CODE_AI_RULES.md" || exit 1; \
		echo "  + Created symlink: ARCH2CODE_AI_RULES.md -> $(A2C_BASE_REL)/ARCH2CODE_AI_RULES.md"; \
	else \
		echo "  = ARCH2CODE_AI_RULES.md already exists in project root"; \
	fi; \
	new="$$R/.cursorrules.new"; \
	printf '%s\n' "# arch2code Project Rules" "" "See .cursor/rules/ for project rules and .cursor/skills/ for skills." > "$$new" || \
	{ echo "  ! Failed to write .cursorrules"; exit 1; }; \
	if a2c_install "$$new" .cursorrules; then echo "  + Wrote .cursorrules"; fi; \
	for root in $(A2C_RULES_DIRS); do \
		for f in "$$root"/*.md; do \
			if [ -f "$$f" ]; then a2c_install "$$f" ".cursor/rules/$$(basename "$$f" .md).mdc"; fi; \
		done; \
	done; \
	echo "  + Installed rules to .cursor/rules/"; \
	for dir in .claude .gemini .opencode .agents .cursor; do \
		for root in $(A2C_RULES_DIRS); do \
			for f in "$$root"/skills/*.md; do \
				if [ -f "$$f" ]; then a2c_install "$$f" "$$dir/skills/$$(basename "$$f" .md)/SKILL.md"; fi; \
			done; \
		done; \
		echo "  + Installed skills to $$dir/skills/"; \
	done; \
	echo ""; \
	echo "Agent setup complete!"; \
	echo ""; \
	echo "Deployed for:"; \
	echo "  - Claude Code    : CLAUDE.md, .claude/skills/"; \
	echo "  - Gemini CLI     : GEMINI.md, .gemini/skills/"; \
	echo "  - OpenCode       : AGENTS.md, .opencode/skills/"; \
	echo "  - Cursor IDE     : .cursorrules, .cursor/rules/, .cursor/skills/"; \
	echo "  - Cross-tool     : .agents/skills/"; \
	echo ""; \
	echo "Reference documentation:"; \
	echo "  - $(A2C_BASE_REL)/ARCH2CODE_AI_RULES.md"; \
	echo "  - $(A2C_BASE_REL)/SYSTEMC_API_USER_REFERENCE.md"; \
	a2c_setup_note agents-clean agents-setup

cursor-setup cursor_setup: agents-setup

#------------------------------------------------------------------------
# agent-dev-setup: Arch2Code builder/base development skills for all platforms
#------------------------------------------------------------------------
agent-dev-setup agent_dev_setup:
	@# CONTEXT.md ships beside wait-what so the skill reads it without naming a
	@# submodule path, which the host project chooses.
	@$(A2C_AGENTS_SH); \
	echo "Setting up Arch2Code builder/base development skills..."; \
	for dir in .claude .gemini .opencode .agents .cursor; do \
		for root in $(A2C_RULES_DIRS); do \
			for f in "$$root"/dev-skills/*.md; do \
				if [ -f "$$f" ]; then a2c_install "$$f" "$$dir/skills/$$(basename "$$f" .md)/SKILL.md"; fi; \
			done; \
		done; \
		if [ -f "$(A2C_BASE_DIR)/CONTEXT.md" ] && [ -d "$$R/$$dir/skills/wait-what" ]; then \
			a2c_install "$(A2C_BASE_DIR)/CONTEXT.md" "$$dir/skills/wait-what/CONTEXT.md"; \
		fi; \
		echo "  + Installed dev skills to $$dir/skills/"; \
	done; \
	echo ""; \
	echo "Arch2Code builder/base development skill setup complete!"; \
	a2c_setup_note agent-dev-clean agent-dev-setup

#------------------------------------------------------------------------
# agent-dev-clean: Remove Arch2Code builder/base development skills
#------------------------------------------------------------------------
agent-dev-clean agent_dev_clean:
	@$(A2C_AGENTS_SH); \
	echo "Removing Arch2Code builder/base development skills..."; \
	for dir in .claude .gemini .opencode .agents .cursor; do \
		if [ -f "$(A2C_BASE_DIR)/CONTEXT.md" ]; then a2c_remove "$$dir/skills/wait-what/CONTEXT.md"; fi; \
		for root in $(A2C_RULES_DIRS); do \
			for f in "$$root"/dev-skills/*.md; do \
				if [ -f "$$f" ]; then \
					sname=$$(basename "$$f" .md); \
					a2c_remove "$$dir/skills/$$sname/SKILL.md"; \
					if [ -d "$$R/$$dir/skills/$$sname" ] && [ -z "$$(ls -A "$$R/$$dir/skills/$$sname")" ]; then rmdir "$$R/$$dir/skills/$$sname"; fi; \
				fi; \
			done; \
		done; \
		a2c_count "$$dir/skills" skill; \
		a2c_rmdir "$$dir/skills"; \
		a2c_rmdir "$$dir"; \
	done; \
	a2c_clean_note agent-dev-clean; \
	echo "Arch2Code builder/base development skill cleanup complete!"

#------------------------------------------------------------------------
# agents-clean: Remove what agents-setup deploys
#
# Besides the files the shipped sources name, it takes every manifest entry
# outside the current dev skills, so a skill dropped or renamed upstream goes
# too.
#------------------------------------------------------------------------
agents-clean agents_clean:
	@$(A2C_AGENTS_SH); \
	echo "Removing AI agent setup files..."; \
	if [ -L "$$R/CLAUDE.md" ]; then \
		rm "$$R/CLAUDE.md" || exit 1; \
		echo "  - Removed CLAUDE.md symlink"; \
	fi; \
	if [ -L "$$R/GEMINI.md" ]; then \
		rm "$$R/GEMINI.md" || exit 1; \
		echo "  - Removed GEMINI.md symlink"; \
	fi; \
	if [ -L "$$R/ARCH2CODE_AI_RULES.md" ]; then \
		rm "$$R/ARCH2CODE_AI_RULES.md" || exit 1; \
		echo "  - Removed ARCH2CODE_AI_RULES.md symlink"; \
	fi; \
	if a2c_remove .cursorrules; then echo "  - Removed .cursorrules"; fi; \
	list=""; \
	for root in $(A2C_RULES_DIRS); do \
		for f in "$$root"/*.md; do \
			if [ -f "$$f" ]; then list="$$list .cursor/rules/$$(basename "$$f" .md).mdc"; fi; \
		done; \
	done; \
	for dir in .claude .gemini .opencode .agents .cursor; do \
		for root in $(A2C_RULES_DIRS); do \
			for f in "$$root"/skills/*.md; do \
				if [ -f "$$f" ]; then list="$$list $$dir/skills/$$(basename "$$f" .md)/SKILL.md"; fi; \
			done; \
		done; \
	done; \
	dev=""; \
	for root in $(A2C_RULES_DIRS); do \
		for f in "$$root"/dev-skills/*.md; do \
			if [ -f "$$f" ]; then dev="$$dev $$(basename "$$f" .md)"; fi; \
		done; \
	done; \
	if [ -f "$$M" ]; then \
		for rel in $$(cut -c35- "$$M"); do \
			case "$$rel" in AGENTS.md|.cursorrules) continue;; esac; \
			for s in $$dev; do case "$$rel" in */skills/$$s/*) continue 2;; esac; done; \
			list="$$list $$rel"; \
		done; \
	fi; \
	for rel in $$(printf '%s\n' $$list | awk '!seen[$$0]++'); do \
		a2c_remove "$$rel"; \
		case "$$rel" in */skills/*/*) \
			d="$$R/$$(dirname "$$rel")"; \
			if [ -d "$$d" ] && [ -z "$$(ls -A "$$d")" ]; then rmdir "$$d"; fi;; \
		esac; \
	done; \
	a2c_count .cursor/rules rule; \
	a2c_rmdir .cursor/rules; \
	for dir in .claude .gemini .opencode .agents .cursor; do \
		a2c_count "$$dir/skills" skill; \
		a2c_rmdir "$$dir/skills"; \
		a2c_rmdir "$$dir"; \
	done; \
	if [ -d "$$R/.ai/skills" ]; then \
		rm -rf "$$R/.ai/skills" || exit 1; \
		echo "  - Removed legacy .ai/skills directory"; \
	fi; \
	if [ -d "$$R/.ai" ] && [ -z "$$(ls -A "$$R/.ai")" ]; then \
		rmdir "$$R/.ai" && \
		echo "  - Removed empty .ai directory"; \
	fi; \
	if [ "$(FORCE)" = "1" ] && [ -f "$$R/AGENTS.md" ]; then \
		rm "$$R/AGENTS.md" && a2c_record AGENTS.md && \
		echo "  - Removed AGENTS.md (forced)"; \
	elif a2c_remove AGENTS.md; then \
		echo "  - Removed AGENTS.md"; \
	fi; \
	a2c_clean_note agents-clean; \
	echo "Agent cleanup complete!"

cursor-clean cursor_clean: agents-clean

help::
	@echo "  agents-setup - Set up Claude Code/Gemini CLI/OpenCode/Cursor IDE rules and skills; replaces each deployed file unless its recorded checksum shows you edited it, and leaves an AGENTS.md it did not create in place"
	@echo "  agents-clean - Remove the agent setup files, keeping an AGENTS.md agents-setup did not create and each file whose recorded checksum shows you edited it (FORCE=1 removes AGENTS.md in every case)"
	@echo "  cursor-setup - Alias of agents-setup"
	@echo "  cursor-clean - Alias of agents-clean"
	@echo "  agent-dev-setup - Install Arch2Code builder/base development skills to all platforms; replaces each skill file unless its recorded checksum shows you edited it"
	@echo "  agent-dev-clean - Remove Arch2Code builder/base development skills from all platforms, keeping each file whose recorded checksum shows you edited it"

endif # A2C_INCLUDE_MAKE_A2C_AGENTS_MK_INCLUDED
