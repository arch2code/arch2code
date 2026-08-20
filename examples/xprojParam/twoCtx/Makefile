REPO_ROOT = $(shell git rev-parse --show-toplevel)/examples/xprojParam/twoCtx

include $(REPO_ROOT)/include/make/shared.mk

.PHONY : clean

clean::
	rm -rf $(A2C_SQLDB_DOTFILE) $(A2C_SQLDB_FILE) $(GEN_BUILD_DIR)

.PHONY : subprojects-gen
gen: subprojects-gen
subprojects-gen:
	$(MAKE) -C $(REPO_ROOT)/../dpLeaf gen

clean::
	$(MAKE) -C $(REPO_ROOT)/../dpLeaf clean
