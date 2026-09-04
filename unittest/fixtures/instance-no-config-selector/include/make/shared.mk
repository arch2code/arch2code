# test_error_instance_no_config_selector.py builds a copy of this tree,
# overriding both roots on the make command line; these defaults serve an
# in-place run.
A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/unittest/fixtures/instance-no-config-selector

PROJECTNAME = incTest
TB_TOP_MODULE = incTop
HDL_TOP_MODULE = incTop

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/incProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
