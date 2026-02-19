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

.PHONY: agents-setup agents-clean agents-sync agents-sync-force agents-validate
.PHONY: agents_setup agents_clean agents_sync agents_sync_force agents_validate
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
	@# Create .cursorrules file from template (fallback to default content)
	@if [ ! -e "$(REPO_ROOT)/.cursorrules" ]; then \
		if [ -f "$(A2C_ROOT)/base/.cursorrules.template" ]; then \
			cp "$(A2C_ROOT)/base/.cursorrules.template" "$(REPO_ROOT)/.cursorrules" && \
			echo "  ✓ Created .cursorrules from template"; \
		else \
			echo "# arch2code Project Rules" > "$(REPO_ROOT)/.cursorrules" && \
			echo "" >> "$(REPO_ROOT)/.cursorrules" && \
			echo "See AGENTS.md for comprehensive project rules and guidelines." >> "$(REPO_ROOT)/.cursorrules" && \
			echo "  ✓ Created .cursorrules"; \
		fi \
	else \
		echo "  ℹ .cursorrules already exists"; \
	fi
	@# Create .cursor/rules and .ai/skills directories
	@mkdir -p $(REPO_ROOT)/.cursor/rules
	@mkdir -p $(REPO_ROOT)/.ai/skills
	@if [ -d "$(A2C_ROOT)/base/rules/skills" ]; then \
		for f in $(A2C_ROOT)/base/rules/skills/*.md; do \
			if [ -f "$$f" ]; then \
				fname=$$(basename $$f); \
				cp "$$f" "$(REPO_ROOT)/.cursor/rules/$$fname" && \
				cp "$$f" "$(REPO_ROOT)/.ai/skills/$$fname" && \
				echo "  ✓ Installed skill: $$fname"; \
			fi \
		done \
	else \
		echo "  ℹ No skills found in builder/base/rules/skills"; \
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
	@echo "  - Cursor IDE     : Uses .cursorrules and .cursor/rules/*.md"
	@echo "  - Claude Code    : Uses CLAUDE.md (symlink to AGENTS.md)"
	@echo "  - Gemini CLI     : Uses GEMINI.md (symlink to AGENTS.md)"
	@echo ""
	@echo "Task-specific rules in: builder/base/rules/"
	@echo "Reference documentation:"
	@echo "  - builder/base/ARCH2CODE_AI_RULES.md"
	@echo "  - builder/base/SYSTEMC_API_USER_REFERENCE.md"

# Refresh generated rules/skills from builder templates without overwriting AGENTS.md
agents-sync agents_sync:
	@echo "Syncing AI agent rules and skills from builder/base..."
	@mkdir -p $(REPO_ROOT)/.cursor/rules
	@mkdir -p $(REPO_ROOT)/.ai/skills
	@if [ -d "$(A2C_ROOT)/base/rules/skills" ]; then \
		for f in $(A2C_ROOT)/base/rules/skills/*.md; do \
			if [ -f "$$f" ]; then \
				fname=$$(basename $$f); \
				dst_cursor="$(REPO_ROOT)/.cursor/rules/$$fname"; \
				dst_ai="$(REPO_ROOT)/.ai/skills/$$fname"; \
				if [ -f "$$dst_cursor" ] && cmp -s "$$f" "$$dst_cursor"; then \
					echo "  = Unchanged skill (.cursor/rules): $$fname"; \
				else \
					cp "$$f" "$$dst_cursor" && \
					echo "  ✓ Updated skill (.cursor/rules): $$fname"; \
				fi; \
				if [ -f "$$dst_ai" ] && cmp -s "$$f" "$$dst_ai"; then \
					echo "  = Unchanged skill (.ai/skills): $$fname"; \
				else \
					cp "$$f" "$$dst_ai" && \
					echo "  ✓ Updated skill (.ai/skills): $$fname"; \
				fi; \
			fi \
		done \
	else \
		echo "  ⚠ Warning: No skills found in $(A2C_ROOT)/base/rules/skills"; \
	fi
	@# Warn about stale generated skills not present in source
	@for d in "$(REPO_ROOT)/.cursor/rules" "$(REPO_ROOT)/.ai/skills"; do \
		for f in "$$d"/*.md; do \
			if [ -f "$$f" ]; then \
				fname=$$(basename "$$f"); \
				if [ ! -f "$(A2C_ROOT)/base/rules/skills/$$fname" ]; then \
					echo "  ⚠ Stale generated skill present in $$(basename $$d): $$fname"; \
				fi; \
			fi; \
		done; \
	done
	@if [ ! -e "$(REPO_ROOT)/AGENTS.md" ] && [ -f "$(A2C_ROOT)/base/AGENTS.md.template" ]; then \
		cp "$(A2C_ROOT)/base/AGENTS.md.template" "$(REPO_ROOT)/AGENTS.md" && \
		echo "  ✓ Created missing AGENTS.md from template"; \
	fi
	@if [ ! -e "$(REPO_ROOT)/.cursorrules" ]; then \
		if [ -f "$(A2C_ROOT)/base/.cursorrules.template" ]; then \
			cp "$(A2C_ROOT)/base/.cursorrules.template" "$(REPO_ROOT)/.cursorrules" && \
			echo "  ✓ Created missing .cursorrules from template"; \
		fi \
	fi
	@if [ ! -L "$(REPO_ROOT)/CLAUDE.md" ] && [ ! -e "$(REPO_ROOT)/CLAUDE.md" ]; then \
		ln -s AGENTS.md $(REPO_ROOT)/CLAUDE.md && \
		echo "  ✓ Created missing CLAUDE.md symlink"; \
	fi
	@if [ ! -L "$(REPO_ROOT)/GEMINI.md" ] && [ ! -e "$(REPO_ROOT)/GEMINI.md" ]; then \
		ln -s AGENTS.md $(REPO_ROOT)/GEMINI.md && \
		echo "  ✓ Created missing GEMINI.md symlink"; \
	fi
	@if [ ! -L "$(REPO_ROOT)/ARCH2CODE_AI_RULES.md" ] && [ ! -e "$(REPO_ROOT)/ARCH2CODE_AI_RULES.md" ]; then \
		ln -s builder/base/ARCH2CODE_AI_RULES.md $(REPO_ROOT)/ARCH2CODE_AI_RULES.md && \
		echo "  ✓ Created missing ARCH2CODE_AI_RULES.md symlink"; \
	fi
	@echo "AI agent sync complete."

# Force refresh AGENTS.md/.cursorrules and rules/skills from templates
agents-sync-force agents_sync_force:
	@echo "Force syncing AI agent rules and skills from builder/base..."
	@if [ -f "$(A2C_ROOT)/base/AGENTS.md.template" ]; then \
		cp "$(A2C_ROOT)/base/AGENTS.md.template" "$(REPO_ROOT)/AGENTS.md" && \
		echo "  ✓ Overwrote AGENTS.md from template"; \
	else \
		echo "  ⚠ Warning: AGENTS.md.template not found"; \
	fi
	@if [ -f "$(A2C_ROOT)/base/.cursorrules.template" ]; then \
		cp "$(A2C_ROOT)/base/.cursorrules.template" "$(REPO_ROOT)/.cursorrules" && \
		echo "  ✓ Overwrote .cursorrules from template"; \
	else \
		echo "  ⚠ Warning: .cursorrules.template not found"; \
	fi
	@$(MAKE) agents-sync
	@# Remove stale generated skill files not present in source
	@for d in "$(REPO_ROOT)/.cursor/rules" "$(REPO_ROOT)/.ai/skills"; do \
		for f in "$$d"/*.md; do \
			if [ -f "$$f" ]; then \
				fname=$$(basename "$$f"); \
				if [ ! -f "$(A2C_ROOT)/base/rules/skills/$$fname" ]; then \
					rm -f "$$f" && \
					echo "  ✓ Removed stale generated skill from $$(basename $$d): $$fname"; \
				fi; \
			fi; \
		done; \
	done

# Validate routing consistency between AGENTS template and installed skills
agents-validate agents_validate:
	@echo "Validating AI agent template and skill consistency..."
	@errors=0; \
	skill_dir="$(A2C_ROOT)/base/rules/skills"; \
	agents_tpl="$(A2C_ROOT)/base/AGENTS.md.template"; \
	if [ ! -f "$$agents_tpl" ]; then \
		echo "  ✗ Missing AGENTS template: $$agents_tpl"; \
		errors=1; \
	fi; \
	if [ ! -d "$$skill_dir" ]; then \
		echo "  ✗ Missing skill directory: $$skill_dir"; \
		errors=1; \
	fi; \
	if [ "$$errors" -eq 0 ]; then \
		refs=$$(sed -n 's/.*`\([^`]*\.md\)`.*/\1/p' "$$agents_tpl" | sort -u); \
		for ref in $$refs; do \
			if [ "$$ref" = "AGENTS.md" ]; then \
				continue; \
			fi; \
			if [ ! -f "$$skill_dir/$$ref" ]; then \
				echo "  ✗ Missing skill referenced in AGENTS template: $$ref"; \
				errors=1; \
			fi; \
		done; \
		dupes=$$(awk -F'|' '/^\| \*\*/ {k=$$2; gsub(/\*/,"",k); gsub(/^[ \t]+|[ \t]+$$/,"",k); print k}' "$$agents_tpl" | sort | uniq -d); \
		if [ -n "$$dupes" ]; then \
			echo "  ✗ Duplicate routing intents found:"; \
			echo "$$dupes" | while IFS= read -r d; do echo "    - $$d"; done; \
			errors=1; \
		fi; \
	fi; \
	cursor_line=$$(awk '/Cursor IDE/ {print; exit}' "$(A2C_ROOT)/include/make/a2c-agents.mk"); \
	case "$$cursor_line" in \
		*"*.mdc"*) advertised_ext=".mdc" ;; \
		*"*.md"*) advertised_ext=".md" ;; \
		*) advertised_ext="unknown" ;; \
	esac; \
	if [ "$$advertised_ext" != ".md" ]; then \
		echo "  ✗ Cursor file extension mismatch: setup advertises $$advertised_ext but installed skills are .md"; \
		errors=1; \
	fi; \
	if [ "$$errors" -ne 0 ]; then \
		echo "Validation failed."; \
		exit 1; \
	fi; \
	echo "Validation passed."

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
	@if [ -d "$(REPO_ROOT)/.ai/skills" ]; then \
		rm -rf $(REPO_ROOT)/.ai/skills && \
		echo "  ✓ Removed .ai/skills directory"; \
	fi
	@if [ -d "$(REPO_ROOT)/.ai" ] && [ -z "$$(ls -A $(REPO_ROOT)/.ai 2>/dev/null)" ]; then \
		rmdir $(REPO_ROOT)/.ai && \
		echo "  ✓ Removed empty .ai directory"; \
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
	@echo "  agents-sync - Sync skills/rules from builder templates"
	@echo "  agents-sync-force - Force overwrite AGENTS/.cursorrules, then sync"
	@echo "  agents-validate - Validate AGENTS routing and setup consistency"
	@echo "  agents-clean - Remove AI agent setup files"
	@echo "  cursor-setup - Alias for agents-setup (backward compatibility)"
	@echo "  cursor-clean - Alias for agents-clean (backward compatibility)"

endif # A2C_INCLUDE_MAKE_A2C_AGENTS_MK_INCLUDED
