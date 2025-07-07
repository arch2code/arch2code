# Makefile variables and targets used in other Makefiles

# Use the following lines to include this shared file from the caller Makefile
####  REPO_ROOT = $(shell git rev-parse --show-toplevel)
####  PROJECT_NAME = <name of the example project>
####  PROJECT_ROOT = $(REPO_ROOT)/examples/$(PROJECT_NAME)
####  include $(REPO_ROOT)/examples/include/shared.mk

# The following env variables need to be defined as well by the caller Makefile
ifndef REPO_ROOT
$(error REPO_ROOT is not set)
endif
ifndef PROJECT_ROOT
$(error PROJECT_ROOT is not set)
endif
ifndef PROJECT_NAME
$(error PROJECT_NAME is not set)
endif

DB_FILE = $(PROJECT_ROOT)/$(PROJECT_NAME).db
DOT_DB_FILE = $(PROJECT_ROOT)/.$(PROJECT_NAME).db

YAML_FILES = $(shell find $(PROJECT_ROOT)/arch -type f -name '*.yaml')
PROJ_FILE = $(PROJECT_ROOT)/arch/$(PROJECT_NAME)Project.yaml

.PHONY: db db-clean

# the inclusion of $(CONTAINER-PREREQUISITES) as a prerequisite here is a trick. If run at the top this will make
#  sure the container is updated, install python libs + git config safe, when run from the top. If run from any
#  other location this variable will not be defined and it will be an empty string and creates no prerequisite for
#  $(DOT_DB_FILE) to be created
$(DOT_DB_FILE): $(YAML_FILES) $(CONTAINER-PREREQUISITES)
	$(REPO_ROOT)/arch2code.py --yaml $(PROJ_FILE) --db $(DB_FILE) && touch $@

db: $(DOT_DB_FILE)

db-clean:
	$(RM) $(DOT_DB_FILE)
	$(RM) $(DB_FILE)
