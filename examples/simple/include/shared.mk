# Makefile variables used in other Makefiles

# In order to find this file each Makefile needs to discover $(REPO_ROOT) and include it
#  therefore $(REPO_ROOT) is already defined
#
# Use the following two lines to include this shared file
####  REPO_ROOT = $(shell git rev-parse --show-toplevel)
####  include $(REPO_ROOT)/include/shared.mk

# check if dir in arg exists
define dir_exists
$(shell test -d $(1) && echo $(1))
endef
# Check if optional.mk exists
A2CPRO_MK := $(wildcard $(REPO_ROOT)/builder/a2cPro.mk)
GREEN := $(shell tput setaf 2)
RESET := $(shell tput sgr0)
ifneq ($(A2CPRO_MK),)
# Optionally include the makefile
$(info $(GREEN)a2cPro build$(RESET) Including $(A2CPRO_MK)) 
include $(A2CPRO_MK)
else
$(info $(GREEN)Non a2cPro build$(RESET)) 
endif
# Shared between ascari & aura
A2C_SRC_DIRS = simple pipe
TB_SRC_DIRS = 

PROJDIR = $(REPO_ROOT)/examples/simple
PROJNAME = simple
PROJNAMEUPPER = SIMPLE
TOPNAME = $(PROJNAME)Top
DB_FILE = $(PROJDIR)/$(PROJNAME).db
DOT_DB_FILE = $(PROJDIR)/.$(PROJNAME).db
#find all the yaml files in the arch/yaml A2C_SRC_DIRS
YAML_FILES = $(shell find $(foreach dir, $(A2C_SRC_DIRS) config, $(call dir_exists, $(PROJDIR)/arch/yaml/$(dir))) -type f -name '*.yaml')
#$(info YAML_FILES=$(YAML_FILES))
PROJ_FILE = $(PROJDIR)/arch/yaml/$(PROJNAME)Proj.yaml
ifdef SAAS_ENV
NO_GEN = true
endif
ifndef NO_GEN
A2C_EXE = $(REPO_ROOT)/arch2code.py
else
A2C_EXE = @true
endif
.PHONY: db db-clean

# the inclusion of $(CONTAINER-PREREQUISITES) as a prerequisite here is a trick. If run at the top this will make
#  sure the container is updated, install python libs + git config safe, when run from the top. If run from any
#  other location this variable will not be defined and it will be an empty string and creates no prerequisite for
#  $(DOT_DB_FILE) to be created
$(DOT_DB_FILE): $(YAML_FILES) $(CONTAINER-PREREQUISITES)
	$(A2C_EXE) --yaml $(PROJ_FILE) --db $(DB_FILE) && touch $(DOT_DB_FILE)

db: $(DOT_DB_FILE) 

db-clean:
	$(RM) $(DB_FILE)
	$(RM) $(DOT_DB_FILE)
