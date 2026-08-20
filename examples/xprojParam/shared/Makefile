REPO_ROOT = $(shell git rev-parse --show-toplevel)/examples/xprojParam/shared

include $(REPO_ROOT)/include/make/shared.mk

.PHONY : clean

clean::
	rm -rf $(A2C_SQLDB_DOTFILE) $(A2C_SQLDB_FILE) $(GEN_BUILD_DIR)

# Composed sub-projects generate and clean through their own targets, so this
# project's gen and clean cover the whole composition either way.
.PHONY : subprojects-gen
gen: subprojects-gen
subprojects-gen:
	$(MAKE) -C $(REPO_ROOT)/../filterShared gen
	$(MAKE) -C $(REPO_ROOT)/../sinkShared gen

clean::
	$(MAKE) -C $(REPO_ROOT)/../filterShared clean
	$(MAKE) -C $(REPO_ROOT)/../sinkShared clean
