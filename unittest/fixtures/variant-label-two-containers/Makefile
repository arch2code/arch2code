REPO_ROOT = $(shell git rev-parse --show-toplevel)/unittest/fixtures/variant-label-two-containers

include $(REPO_ROOT)/include/make/shared.mk

.PHONY : clean

clean::
	rm -rf $(A2C_SQLDB_DOTFILE) $(A2C_SQLDB_FILE) $(GEN_BUILD_DIR)
