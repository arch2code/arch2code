REPO_ROOT = $(shell git rev-parse --show-toplevel)/examples/xprojParam/dpTop

include $(REPO_ROOT)/include/make/shared.mk

.PHONY : clean

clean::
	rm -rf $(A2C_SQLDB_DOTFILE) $(A2C_SQLDB_FILE) $(GEN_BUILD_DIR)

# The mid-level IP generates and cleans through its own targets, which in turn
# cover the leaf.
.PHONY : subprojects-gen
gen: subprojects-gen
subprojects-gen:
	$(MAKE) -C $(REPO_ROOT)/../dpMid gen

clean::
	$(MAKE) -C $(REPO_ROOT)/../dpMid clean
