REPO_ROOT = $(shell git rev-parse --show-toplevel)/examples/xprojParam/mtxComp

include $(REPO_ROOT)/include/make/shared.mk

.PHONY : clean

clean::
	rm -rf $(A2C_SQLDB_DOTFILE) $(A2C_SQLDB_FILE) $(GEN_BUILD_DIR)

# The reused container's own project generates and cleans through its own
# targets, so this project's gen and clean cover the whole composition.
.PHONY : subprojects-gen
gen: subprojects-gen
subprojects-gen:
	$(MAKE) -C $(REPO_ROOT)/../mtxElect gen

clean::
	$(MAKE) -C $(REPO_ROOT)/../mtxElect clean
