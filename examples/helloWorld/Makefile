REPO_ROOT = $(shell git rev-parse --show-toplevel)/examples/helloWorld

include $(REPO_ROOT)/include/make/shared.mk

.PHONY : reset clean

# `reset` wipes generated trees so that the next `make db` regenerates everything.
# helloWorld only generates into `base/` (block base classes) and the *Includes.*
# files inside `model/`. User source files in `model/` are NOT deleted.
reset: clean
	rm -rf $(REPO_ROOT)/base
	rm -f  $(REPO_ROOT)/model/*Includes.cpp $(REPO_ROOT)/model/*Includes.h

clean::
	rm -rf $(A2C_SQLDB_DOTFILE) $(A2C_SQLDB_FILE) $(GEN_BUILD_DIR)
