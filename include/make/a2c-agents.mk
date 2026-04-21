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
#   agents-setup  : Claude Code, Gemini CLI, OpenCode (.claude/, .gemini/, .opencode/, .agents/)
#   cursor-setup  : Cursor IDE (.cursorrules, .cursor/rules/, .cursor/skills/)
#   agents-clean  : Remove OpenCode/generic agent artifacts
#   cursor-clean  : Remove Cursor IDE artifacts (rules, skills, .cursorrules)
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
	@# Deploy skills to each platform's expected layout:
	@#   Claude Code:  .claude/skills/{name}/SKILL.md
	@#   Gemini CLI:   .gemini/skills/{name}/SKILL.md
	@#   OpenCode:     .opencode/skills/{name}/SKILL.md
	@#   Cross-tool:   .agents/skills/{name}/SKILL.md
	@if [ -d "$(A2C_ROOT)/base/rules/skills" ]; then \
		for dir in .claude .gemini .opencode .agents; do \
			mkdir -p "$(REPO_ROOT)/$$dir/skills"; \
			for f in $(A2C_ROOT)/base/rules/skills/*.md; do \
				if [ -f "$$f" ]; then \
					sname=$$(basename $$f .md); \
					mkdir -p "$(REPO_ROOT)/$$dir/skills/$$sname" && \
					cp "$$f" "$(REPO_ROOT)/$$dir/skills/$$sname/SKILL.md"; \
				fi \
			done; \
			echo "  + Installed skills to $$dir/skills/"; \
		done \
	else \
		echo "  = No skills found in builder/base/rules/skills"; \
	fi
	@echo ""
	@echo "Agent setup complete!"
	@echo ""
	@echo "Deployed for:"
	@echo "  - Claude Code    : CLAUDE.md, .claude/skills/"
	@echo "  - Gemini CLI     : GEMINI.md, .gemini/skills/"
	@echo "  - OpenCode       : AGENTS.md, .opencode/skills/"
	@echo "  - Cross-tool     : .agents/skills/"
	@echo ""
	@echo "Reference documentation:"
	@echo "  - builder/base/ARCH2CODE_AI_RULES.md"
	@echo "  - builder/base/SYSTEMC_API_USER_REFERENCE.md"

#------------------------------------------------------------------------
# cursor-setup: Cursor IDE
#------------------------------------------------------------------------
cursor-setup cursor_setup:
	@echo "Setting up Cursor IDE rules and skills..."
	@# Create .cursorrules file
	@if [ ! -e "$(REPO_ROOT)/.cursorrules" ]; then \
		echo "# arch2code Project Rules" > $(REPO_ROOT)/.cursorrules && \
		echo "" >> $(REPO_ROOT)/.cursorrules && \
		echo "See .cursor/rules/ for project rules and skill files." >> $(REPO_ROOT)/.cursorrules && \
		echo "  + Created .cursorrules"; \
	else \
		echo "  = .cursorrules already exists"; \
	fi
	@# Deploy rules to .cursor/rules/ (flat copy, .md -> .mdc)
	@mkdir -p $(REPO_ROOT)/.cursor/rules
	@if ls $(A2C_ROOT)/base/rules/*.md 1>/dev/null 2>&1; then \
		for f in $(A2C_ROOT)/base/rules/*.md; do \
			if [ -f "$$f" ]; then \
				fname=$$(basename $$f .md).mdc; \
				cp "$$f" "$(REPO_ROOT)/.cursor/rules/$$fname" && \
				echo "  + Installed Cursor rule: $$fname"; \
			fi \
		done \
	else \
		echo "  = No rules found in builder/base/rules/"; \
	fi
	@# Deploy skills to .cursor/skills/{name}/SKILL.md (directory per skill)
	@mkdir -p $(REPO_ROOT)/.cursor/skills
	@if [ -d "$(A2C_ROOT)/base/rules/skills" ]; then \
		for f in $(A2C_ROOT)/base/rules/skills/*.md; do \
			if [ -f "$$f" ]; then \
				sname=$$(basename $$f .md); \
				mkdir -p "$(REPO_ROOT)/.cursor/skills/$$sname" && \
				cp "$$f" "$(REPO_ROOT)/.cursor/skills/$$sname/SKILL.md" && \
				echo "  + Installed Cursor skill: $$sname"; \
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
	@echo "  - .cursor/rules/*.mdc  (auto-applied rules with globs frontmatter)"
	@echo "  - .cursor/skills/*/SKILL.md (on-demand skills)"

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
	@# Remove skills from all platform directories
	@for dir in .claude .gemini .opencode .agents; do \
		if [ -d "$(REPO_ROOT)/$$dir/skills" ]; then \
			rm -rf "$(REPO_ROOT)/$$dir/skills" && \
			echo "  - Removed $$dir/skills directory"; \
		fi; \
		if [ -d "$(REPO_ROOT)/$$dir" ] && [ -z "$$(ls -A "$(REPO_ROOT)/$$dir" 2>/dev/null)" ]; then \
			rmdir "$(REPO_ROOT)/$$dir" && \
			echo "  - Removed empty $$dir directory"; \
		fi; \
	done
	@# Clean up legacy .ai/skills/ if present
	@if [ -d "$(REPO_ROOT)/.ai/skills" ]; then \
		rm -rf $(REPO_ROOT)/.ai/skills && \
		echo "  - Removed legacy .ai/skills directory"; \
	fi
	@if [ -d "$(REPO_ROOT)/.ai" ] && [ -z "$$(ls -A $(REPO_ROOT)/.ai 2>/dev/null)" ]; then \
		rmdir $(REPO_ROOT)/.ai && \
		echo "  - Removed empty .ai directory"; \
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
	@if [ -d "$(REPO_ROOT)/.cursor/skills" ]; then \
		rm -rf $(REPO_ROOT)/.cursor/skills && \
		echo "  - Removed .cursor/skills directory"; \
	fi
	@if [ -d "$(REPO_ROOT)/.cursor" ] && [ -z "$$(ls -A $(REPO_ROOT)/.cursor 2>/dev/null)" ]; then \
		rmdir $(REPO_ROOT)/.cursor && \
		echo "  - Removed empty .cursor directory"; \
	fi
	@echo "Cursor cleanup complete!"

help::
	@echo "  agents-setup - Setup Claude Code/Gemini CLI/OpenCode rules and skills"
	@echo "  agents-clean - Remove agent setup files (FORCE=1 to remove modified AGENTS.md)"
	@echo "  cursor-setup - Setup Cursor IDE rules (.cursor/rules/) and skills (.cursor/skills/)"
	@echo "  cursor-clean - Remove Cursor IDE setup files (rules, skills, .cursorrules)"

endif # A2C_INCLUDE_MAKE_A2C_AGENTS_MK_INCLUDED
