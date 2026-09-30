REPO_ROOT = $(shell git rev-parse --show-toplevel)/examples/simple_ip

include $(REPO_ROOT)/include/make/shared.mk

.PHONY : clean

clean::
	rm -rf $(A2C_SQLDB_DOTFILE) $(A2C_SQLDB_FILE) $(GEN_BUILD_DIR)

# Composed sub-projects generate and clean through their own targets, so this
# project's gen and clean cover the whole composition either way.
.PHONY : subprojects-gen
gen: subprojects-gen
subprojects-gen:
	$(MAKE) -C $(REPO_ROOT)/common gen
	$(MAKE) -C $(REPO_ROOT)/ip gen

clean::
	$(MAKE) -C $(REPO_ROOT)/common clean
	$(MAKE) -C $(REPO_ROOT)/ip clean
