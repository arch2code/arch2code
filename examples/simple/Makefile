REPO_ROOT = $(shell git rev-parse --show-toplevel)
CONTAINER-PREREQUISITES = $(REPO_ROOT)/.container-prerequisites

include $(REPO_ROOT)/examples/simple/include/shared.mk

.DEFAULT_GOAL := all

# file to test if in a container, otherwise treat as if it is a bitbucket pipeline run
#  source for usage of wildcard and ifneq; https://stackoverflow.com/a/20566812/8980882
#  the CONTAINER-PREREQUISITES rule below uses the varaible FILE_EXISTS to
#  skip installing python libraries and setting git config
PATH_TO_FILE = /.dockerenv

ifneq ("$(wildcard $(PATH_TO_FILE))","")
    FILE_EXISTS = 1
    .PHONY: spec clean doc model modelrun modellog modelnolog deep-clean rtl verif fpga setup all
else
    FILE_EXISTS = 0
    # /.dockerenv added so it is not treated as a rule when the file does not exist
    .PHONY: spec clean doc model modelrun modellog modelnolog deep-clean rtl verif fpga setup all /.dockerenv
endif

# all rule set to only run spec, doc is broken, and model and spec run longer than 3 minutes
all: spec model rtl verif

spec: $(CONTAINER-PREREQUISITES) $(DOT_DB_FILE)
	make -C arch

clean: $(CONTAINER-PREREQUISITES) db-clean
#	make -C arch clean
#	make -C model clean
#	make -C verif clean

deep-clean: $(CONTAINER-PREREQUISITES) clean
	make -C arch deep-clean

doc: $(CONTAINER-PREREQUISITES) $(DOT_DB_FILE)
	$(A2C_EXE) --db $(DB_FILE) --readonly --docgen

# this is intended to be used inside the docker container until the model/Makefile
# dependencies get fixed
model: $(CONTAINER-PREREQUISITES) $(DOT_DB_FILE)
	make -C model

# run model with reduced logging 
modelrun: model
	$(MAKE) -C model run RUN_OPTS=" --log --verbosity=medium"

# run model with no logging 
modelnolog: model
	$(MAKE) -C model run RUN_OPTS=" --log --verbosity=low"

# run model with normal logging
modellog: model
	$(MAKE) -C model run RUN_OPTS=" --log"

rtl: $(CONTAINER-PREREQUISITES) $(DOT_DB_FILE)
	make -C rtl

verif: $(CONTAINER-PREREQUISITES) $(DOT_DB_FILE)
	$(MAKE) -C verif all

fpga:
	$(MAKE) -C fpga all

setup: $(CONTAINER-PREREQUISITES) 

.PHONY : dockerImage dockerRun
dockerImage:
	docker build -t $(USER)/ascari . --build-arg USERNAME=$(USER) --build-arg USER_UID=$(shell id -u) --build-arg USER_GID=$(shell id -g)

dockerRun:
	docker run --rm -ti -v $(PWD):/work --user $(USER) --hostname $$(basename $(PWD)) --workdir "/work" --entrypoint /bin/bash $(USER)/ascari

# this rule will only run the first time into a docker container
$(CONTAINER-PREREQUISITES): /.dockerenv
ifeq ($(FILE_EXISTS),1)
	git config --global --add safe.directory $(REPO_ROOT)
	pip3 install -r $(REPO_ROOT)/requirements.txt
endif
	touch $@
