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
# Cursor AI Setup Targets
#------------------------------------------------------------------------

.PHONY: cursor_setup cursor_clean cursor-setup cursor-clean

# Setup Cursor AI rules for arch2code development
cursor_setup cursor-setup:
	@echo "Setting up Cursor AI rules for arch2code..."
	@# Create symlink to ARCH2CODE_AI_RULES.md in project root
	@if [ ! -L "$(REPO_ROOT)/ARCH2CODE_AI_RULES.md" ] && [ ! -e "$(REPO_ROOT)/ARCH2CODE_AI_RULES.md" ]; then \
		ln -s builder/base/ARCH2CODE_AI_RULES.md $(REPO_ROOT)/ARCH2CODE_AI_RULES.md && \
		echo "  ✓ Created symlink: ARCH2CODE_AI_RULES.md -> builder/base/ARCH2CODE_AI_RULES.md"; \
	else \
		echo "  ℹ ARCH2CODE_AI_RULES.md already exists in project root"; \
	fi
	@# Create .cursorrules file from template
	@if [ ! -e "$(REPO_ROOT)/.cursorrules" ]; then \
		cp $(A2C_ROOT)/base/.cursorrules.template $(REPO_ROOT)/.cursorrules && \
		echo "  ✓ Created .cursorrules file"; \
	else \
		echo "  ℹ .cursorrules already exists"; \
	fi
	@echo ""
	@echo "Cursor AI setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Reload Cursor to pick up .cursorrules"
	@echo "  2. Review ARCH2CODE_AI_RULES.md for complete guidelines"
	@echo "  3. Ensure AI assistant has access to builder/base/config/schema.yaml"

# Remove Cursor AI setup files
cursor_clean cursor-clean:
	@echo "Removing Cursor AI setup files..."
	@if [ -L "$(REPO_ROOT)/ARCH2CODE_AI_RULES.md" ]; then \
		rm $(REPO_ROOT)/ARCH2CODE_AI_RULES.md && \
		echo "  ✓ Removed ARCH2CODE_AI_RULES.md symlink"; \
	fi
	@if [ -f "$(REPO_ROOT)/.cursorrules" ]; then \
		rm $(REPO_ROOT)/.cursorrules && \
		echo "  ✓ Removed .cursorrules"; \
	fi
	@echo "Cursor AI cleanup complete!"

help::
	@echo "  cursor-setup - Setup Cursor AI rules and guidelines"
	@echo "  cursor-clean - Remove Cursor AI setup files"

