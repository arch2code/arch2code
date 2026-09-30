# test_regs_handler_container_config.py builds a copy of this tree, overriding
# both roots on the make command line; these defaults serve an in-place run.
A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/unittest/fixtures/regs-container-variant

PROJECTNAME = rcvTest
TB_TOP_MODULE = rcvTop
HDL_TOP_MODULE = rcvTop

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/rcvProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
