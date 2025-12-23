REPO_ROOT = $(shell git rev-parse --show-toplevel)/examples/mixed

include $(REPO_ROOT)/include/make/shared.mk

.PHONY : reset clean

reset: clean
	rm -rf $(REPO_ROOT)/base $(REPO_ROOT)/model $(REPO_ROOT)/tb $(REPO_ROOT)/rtl $(REPO_ROOT)/verif

clean::
	rm -rf $(A2C_SQLDB_DOTFILE) $(A2C_SQLDB_FILE) $(GEN_BUILD_DIR)
