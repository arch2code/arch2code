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
# AI Agent Setup Targets (Portable across tools)
#------------------------------------------------------------------------

.PHONY: agents-setup agents-clean agents_setup agents_clean
.PHONY: cursor-setup cursor-clean cursor_setup cursor_clean

# Setup AI agent rules for arch2code development
# Supports: Cursor, Claude Code, Gemini CLI, and other AI coding tools
agents-setup agents_setup:
	@echo "Setting up AI agent rules for arch2code..."
	@# Create AGENTS.md from template (or copy if exists)
	@if [ ! -e "$(REPO_ROOT)/AGENTS.md" ]; then \
		if [ -f "$(A2C_ROOT)/base/AGENTS.md.template" ]; then \
			cp $(A2C_ROOT)/base/AGENTS.md.template $(REPO_ROOT)/AGENTS.md && \
			echo "  ✓ Created AGENTS.md from template"; \
		else \
			echo "  ⚠ Warning: AGENTS.md.template not found - create AGENTS.md manually"; \
		fi \
	else \
		echo "  ℹ AGENTS.md already exists"; \
	fi
	@# Create symlinks for tool-specific files
	@if [ ! -L "$(REPO_ROOT)/CLAUDE.md" ] && [ ! -e "$(REPO_ROOT)/CLAUDE.md" ]; then \
		ln -s AGENTS.md $(REPO_ROOT)/CLAUDE.md && \
		echo "  ✓ Created symlink: CLAUDE.md -> AGENTS.md"; \
	else \
		echo "  ℹ CLAUDE.md already exists"; \
	fi
	@if [ ! -L "$(REPO_ROOT)/GEMINI.md" ] && [ ! -e "$(REPO_ROOT)/GEMINI.md" ]; then \
		ln -s AGENTS.md $(REPO_ROOT)/GEMINI.md && \
		echo "  ✓ Created symlink: GEMINI.md -> AGENTS.md"; \
	else \
		echo "  ℹ GEMINI.md already exists"; \
	fi
	@# Create .cursorrules file
	@if [ ! -e "$(REPO_ROOT)/.cursorrules" ]; then \
		echo "# arch2code Project Rules" > $(REPO_ROOT)/.cursorrules && \
		echo "" >> $(REPO_ROOT)/.cursorrules && \
		echo "See AGENTS.md for comprehensive project rules and guidelines." >> $(REPO_ROOT)/.cursorrules && \
		echo "  ✓ Created .cursorrules"; \
	else \
		echo "  ℹ .cursorrules already exists"; \
	fi
	@# Create .cursor/rules directory and wrapper files
	@mkdir -p $(REPO_ROOT)/.cursor/rules
	@if [ -d "$(A2C_ROOT)/base/cursor-rules-templates" ]; then \
		for f in $(A2C_ROOT)/base/cursor-rules-templates/*.mdc; do \
			if [ -f "$$f" ]; then \
				fname=$$(basename $$f); \
				if [ ! -e "$(REPO_ROOT)/.cursor/rules/$$fname" ]; then \
					cp $$f $(REPO_ROOT)/.cursor/rules/$$fname && \
					echo "  ✓ Created .cursor/rules/$$fname"; \
				else \
					echo "  ℹ .cursor/rules/$$fname already exists"; \
				fi \
			fi \
		done \
	else \
		echo "  ℹ No cursor-rules-templates found - create .cursor/rules/*.mdc manually if needed"; \
	fi
	@# Create symlink to ARCH2CODE_AI_RULES.md in project root (for easy access)
	@if [ ! -L "$(REPO_ROOT)/ARCH2CODE_AI_RULES.md" ] && [ ! -e "$(REPO_ROOT)/ARCH2CODE_AI_RULES.md" ]; then \
		ln -s builder/base/ARCH2CODE_AI_RULES.md $(REPO_ROOT)/ARCH2CODE_AI_RULES.md && \
		echo "  ✓ Created symlink: ARCH2CODE_AI_RULES.md -> builder/base/ARCH2CODE_AI_RULES.md"; \
	else \
		echo "  ℹ ARCH2CODE_AI_RULES.md already exists in project root"; \
	fi
	@echo ""
	@echo "AI agent setup complete!"
	@echo ""
	@echo "Supported tools:"
	@echo "  - Cursor IDE     : Uses .cursorrules and .cursor/rules/*.mdc"
	@echo "  - Claude Code    : Uses CLAUDE.md (symlink to AGENTS.md)"
	@echo "  - Gemini CLI     : Uses GEMINI.md (symlink to AGENTS.md)"
	@echo ""
	@echo "Task-specific rules in: builder/base/rules/"
	@echo "Reference documentation:"
	@echo "  - builder/base/ARCH2CODE_AI_RULES.md"
	@echo "  - builder/base/SYSTEMC_API_USER_REFERENCE.md"

# Remove AI agent setup files
agents-clean agents_clean:
	@echo "Removing AI agent setup files..."
	@if [ -L "$(REPO_ROOT)/CLAUDE.md" ]; then \
		rm $(REPO_ROOT)/CLAUDE.md && \
		echo "  ✓ Removed CLAUDE.md symlink"; \
	fi
	@if [ -L "$(REPO_ROOT)/GEMINI.md" ]; then \
		rm $(REPO_ROOT)/GEMINI.md && \
		echo "  ✓ Removed GEMINI.md symlink"; \
	fi
	@if [ -L "$(REPO_ROOT)/ARCH2CODE_AI_RULES.md" ]; then \
		rm $(REPO_ROOT)/ARCH2CODE_AI_RULES.md && \
		echo "  ✓ Removed ARCH2CODE_AI_RULES.md symlink"; \
	fi
	@if [ -f "$(REPO_ROOT)/.cursorrules" ]; then \
		rm $(REPO_ROOT)/.cursorrules && \
		echo "  ✓ Removed .cursorrules"; \
	fi
	@if [ -d "$(REPO_ROOT)/.cursor/rules" ]; then \
		rm -rf $(REPO_ROOT)/.cursor/rules && \
		echo "  ✓ Removed .cursor/rules directory"; \
	fi
	@if [ -d "$(REPO_ROOT)/.cursor" ] && [ -z "$$(ls -A $(REPO_ROOT)/.cursor 2>/dev/null)" ]; then \
		rmdir $(REPO_ROOT)/.cursor && \
		echo "  ✓ Removed empty .cursor directory"; \
	fi
	@if [ -f "$(REPO_ROOT)/AGENTS.md" ]; then \
		rm $(REPO_ROOT)/AGENTS.md && \
		echo "  ✓ Removed AGENTS.md"; \
	fi
	@echo "AI agent cleanup complete!"

# Backward compatibility aliases
cursor-setup cursor_setup: agents-setup
cursor-clean cursor_clean: agents-clean

help::
	@echo "  agents-setup - Setup AI agent rules (Cursor, Claude Code, Gemini CLI)"
	@echo "  agents-clean - Remove AI agent setup files"
	@echo "  cursor-setup - Alias for agents-setup (backward compatibility)"
	@echo "  cursor-clean - Alias for agents-clean (backward compatibility)"

endif # A2C_INCLUDE_MAKE_A2C_AGENTS_MK_INCLUDED
