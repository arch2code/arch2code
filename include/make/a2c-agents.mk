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
# AI Agent Setup Targets
#
#   agents-setup  : OpenCode, Claude Code, Gemini CLI (AGENTS.md, .opencode/skills/, .ai/skills/)
#   cursor-setup  : Cursor IDE (.cursorrules, .cursor/rules/)
#   agents-clean  : Remove OpenCode/generic agent artifacts
#   cursor-clean  : Remove Cursor IDE artifacts
#------------------------------------------------------------------------

.PHONY: agents-setup agents-clean agents_setup agents_clean
.PHONY: cursor-setup cursor-clean cursor_setup cursor_clean

#------------------------------------------------------------------------
# agents-setup: OpenCode / Claude Code / Gemini CLI / generic agents
#------------------------------------------------------------------------
agents-setup agents_setup:
	@echo "Setting up AI agent rules (OpenCode, Claude Code, Gemini CLI)..."
	@# Create AGENTS.md from template and record its checksum
	@if [ ! -e "$(REPO_ROOT)/AGENTS.md" ]; then \
		if [ -f "$(A2C_ROOT)/base/AGENTS.md.template" ]; then \
			cp $(A2C_ROOT)/base/AGENTS.md.template $(REPO_ROOT)/AGENTS.md && \
			(cd "$(REPO_ROOT)" && md5sum AGENTS.md > .agents-setup.md5) && \
			echo "  + Created AGENTS.md from template"; \
		else \
			echo "  ! Warning: AGENTS.md.template not found - create AGENTS.md manually"; \
		fi \
	else \
		echo "  = AGENTS.md already exists"; \
	fi
	@# Create symlinks for tool-specific entry points
	@if [ ! -L "$(REPO_ROOT)/CLAUDE.md" ] && [ ! -e "$(REPO_ROOT)/CLAUDE.md" ]; then \
		ln -s AGENTS.md $(REPO_ROOT)/CLAUDE.md && \
		echo "  + Created symlink: CLAUDE.md -> AGENTS.md"; \
	else \
		echo "  = CLAUDE.md already exists"; \
	fi
	@if [ ! -L "$(REPO_ROOT)/GEMINI.md" ] && [ ! -e "$(REPO_ROOT)/GEMINI.md" ]; then \
		ln -s AGENTS.md $(REPO_ROOT)/GEMINI.md && \
		echo "  + Created symlink: GEMINI.md -> AGENTS.md"; \
	else \
		echo "  = GEMINI.md already exists"; \
	fi
	@# Create symlink to ARCH2CODE_AI_RULES.md in project root
	@if [ ! -L "$(REPO_ROOT)/ARCH2CODE_AI_RULES.md" ] && [ ! -e "$(REPO_ROOT)/ARCH2CODE_AI_RULES.md" ]; then \
		ln -s builder/base/ARCH2CODE_AI_RULES.md $(REPO_ROOT)/ARCH2CODE_AI_RULES.md && \
		echo "  + Created symlink: ARCH2CODE_AI_RULES.md -> builder/base/ARCH2CODE_AI_RULES.md"; \
	else \
		echo "  = ARCH2CODE_AI_RULES.md already exists in project root"; \
	fi
	@# Deploy skills to .ai/skills/ (flat copy)
	@mkdir -p $(REPO_ROOT)/.ai/skills
	@if [ -d "$(A2C_ROOT)/base/rules/skills" ]; then \
		for f in $(A2C_ROOT)/base/rules/skills/*.md; do \
			if [ -f "$$f" ]; then \
				fname=$$(basename $$f); \
				cp "$$f" "$(REPO_ROOT)/.ai/skills/$$fname" && \
				echo "  + Installed .ai skill: $$fname"; \
			fi \
		done \
	else \
		echo "  = No skills found in builder/base/rules/skills"; \
	fi
	@# Deploy skills to .opencode/skills/{name}/SKILL.md (directory per skill)
	@mkdir -p $(REPO_ROOT)/.opencode/skills
	@if [ -d "$(A2C_ROOT)/base/rules/skills" ]; then \
		for f in $(A2C_ROOT)/base/rules/skills/*.md; do \
			if [ -f "$$f" ]; then \
				sname=$$(basename $$f .md); \
				mkdir -p "$(REPO_ROOT)/.opencode/skills/$$sname" && \
				cp "$$f" "$(REPO_ROOT)/.opencode/skills/$$sname/SKILL.md" && \
				echo "  + Installed OpenCode skill: $$sname"; \
			fi \
		done \
	else \
		echo "  = No skills found in builder/base/rules/skills"; \
	fi
	@echo ""
	@echo "Agent setup complete!"
	@echo ""
	@echo "Deployed for:"
	@echo "  - OpenCode       : AGENTS.md, .opencode/skills/"
	@echo "  - Claude Code    : CLAUDE.md (symlink to AGENTS.md)"
	@echo "  - Gemini CLI     : GEMINI.md (symlink to AGENTS.md)"
	@echo ""
	@echo "Reference documentation:"
	@echo "  - builder/base/ARCH2CODE_AI_RULES.md"
	@echo "  - builder/base/SYSTEMC_API_USER_REFERENCE.md"

#------------------------------------------------------------------------
# cursor-setup: Cursor IDE
#------------------------------------------------------------------------
cursor-setup cursor_setup:
	@echo "Setting up Cursor IDE rules..."
	@# Create .cursorrules file
	@if [ ! -e "$(REPO_ROOT)/.cursorrules" ]; then \
		echo "# arch2code Project Rules" > $(REPO_ROOT)/.cursorrules && \
		echo "" >> $(REPO_ROOT)/.cursorrules && \
		echo "See .cursor/rules/ for project rules and skill files." >> $(REPO_ROOT)/.cursorrules && \
		echo "  + Created .cursorrules"; \
	else \
		echo "  = .cursorrules already exists"; \
	fi
	@# Deploy skills to .cursor/rules/ (flat copy)
	@mkdir -p $(REPO_ROOT)/.cursor/rules
	@if [ -d "$(A2C_ROOT)/base/rules/skills" ]; then \
		for f in $(A2C_ROOT)/base/rules/skills/*.md; do \
			if [ -f "$$f" ]; then \
				fname=$$(basename $$f); \
				cp "$$f" "$(REPO_ROOT)/.cursor/rules/$$fname" && \
				echo "  + Installed Cursor rule: $$fname"; \
			fi \
		done \
	else \
		echo "  = No skills found in builder/base/rules/skills"; \
	fi
	@echo ""
	@echo "Cursor setup complete!"
	@echo ""
	@echo "Deployed:"
	@echo "  - .cursorrules"
	@echo "  - .cursor/rules/*.md (with globs frontmatter for auto-apply)"

#------------------------------------------------------------------------
# agents-clean: Remove OpenCode / generic agent artifacts
#------------------------------------------------------------------------
agents-clean agents_clean:
	@echo "Removing OpenCode/generic agent setup files..."
	@if [ -L "$(REPO_ROOT)/CLAUDE.md" ]; then \
		rm $(REPO_ROOT)/CLAUDE.md && \
		echo "  - Removed CLAUDE.md symlink"; \
	fi
	@if [ -L "$(REPO_ROOT)/GEMINI.md" ]; then \
		rm $(REPO_ROOT)/GEMINI.md && \
		echo "  - Removed GEMINI.md symlink"; \
	fi
	@if [ -L "$(REPO_ROOT)/ARCH2CODE_AI_RULES.md" ]; then \
		rm $(REPO_ROOT)/ARCH2CODE_AI_RULES.md && \
		echo "  - Removed ARCH2CODE_AI_RULES.md symlink"; \
	fi
	@if [ -d "$(REPO_ROOT)/.ai/skills" ]; then \
		rm -rf $(REPO_ROOT)/.ai/skills && \
		echo "  - Removed .ai/skills directory"; \
	fi
	@if [ -d "$(REPO_ROOT)/.ai" ] && [ -z "$$(ls -A $(REPO_ROOT)/.ai 2>/dev/null)" ]; then \
		rmdir $(REPO_ROOT)/.ai && \
		echo "  - Removed empty .ai directory"; \
	fi
	@if [ -d "$(REPO_ROOT)/.opencode/skills" ]; then \
		rm -rf $(REPO_ROOT)/.opencode/skills && \
		echo "  - Removed .opencode/skills directory"; \
	fi
	@if [ -d "$(REPO_ROOT)/.opencode" ] && [ -z "$$(ls -A $(REPO_ROOT)/.opencode 2>/dev/null)" ]; then \
		rmdir $(REPO_ROOT)/.opencode && \
		echo "  - Removed empty .opencode directory"; \
	fi
	@if [ -f "$(REPO_ROOT)/AGENTS.md" ]; then \
		if [ "$(FORCE)" = "1" ]; then \
			rm "$(REPO_ROOT)/AGENTS.md" && \
			echo "  - Removed AGENTS.md (forced)"; \
		elif [ -f "$(REPO_ROOT)/.agents-setup.md5" ] && \
		   (cd "$(REPO_ROOT)" && md5sum --status -c .agents-setup.md5 2>/dev/null); then \
			rm "$(REPO_ROOT)/AGENTS.md" && \
			echo "  - Removed AGENTS.md (unchanged since setup)"; \
		else \
			echo "  ! Skipping AGENTS.md (modified or no checksum; use FORCE=1 to override)"; \
		fi \
	fi
	@if [ -f "$(REPO_ROOT)/.agents-setup.md5" ]; then \
		rm "$(REPO_ROOT)/.agents-setup.md5" && \
		echo "  - Removed .agents-setup.md5"; \
	fi
	@echo "Agent cleanup complete!"

#------------------------------------------------------------------------
# cursor-clean: Remove Cursor IDE artifacts
#------------------------------------------------------------------------
cursor-clean cursor_clean:
	@echo "Removing Cursor IDE setup files..."
	@if [ -f "$(REPO_ROOT)/.cursorrules" ]; then \
		rm $(REPO_ROOT)/.cursorrules && \
		echo "  - Removed .cursorrules"; \
	fi
	@if [ -d "$(REPO_ROOT)/.cursor/rules" ]; then \
		rm -rf $(REPO_ROOT)/.cursor/rules && \
		echo "  - Removed .cursor/rules directory"; \
	fi
	@if [ -d "$(REPO_ROOT)/.cursor" ] && [ -z "$$(ls -A $(REPO_ROOT)/.cursor 2>/dev/null)" ]; then \
		rmdir $(REPO_ROOT)/.cursor && \
		echo "  - Removed empty .cursor directory"; \
	fi
	@echo "Cursor cleanup complete!"

help::
	@echo "  agents-setup - Setup OpenCode/Claude Code/Gemini CLI rules (AGENTS.md, .opencode/skills/)"
	@echo "  agents-clean - Remove OpenCode/generic agent setup files (FORCE=1 to remove modified AGENTS.md)"
	@echo "  cursor-setup - Setup Cursor IDE rules (.cursorrules, .cursor/rules/)"
	@echo "  cursor-clean - Remove Cursor IDE setup files"

endif # A2C_INCLUDE_MAKE_A2C_AGENTS_MK_INCLUDED
