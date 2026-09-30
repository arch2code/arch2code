REPO_ROOT = $(shell git rev-parse --show-toplevel)/examples/xprojParam/rtInh

include $(REPO_ROOT)/include/make/shared.mk

.PHONY : clean

clean::
	rm -rf $(A2C_SQLDB_DOTFILE) $(A2C_SQLDB_FILE) $(GEN_BUILD_DIR)

# The vendored 'common' sub-project generates and cleans through its own
# target, so this project's gen and clean cover the whole composition either
# way.
.PHONY : subprojects-gen
gen: subprojects-gen
subprojects-gen:
	$(MAKE) -C $(REPO_ROOT)/common gen

clean::
	$(MAKE) -C $(REPO_ROOT)/common clean
