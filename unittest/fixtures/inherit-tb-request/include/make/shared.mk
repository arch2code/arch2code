# test_error_inherit_container_tb.py builds a copy of this tree, overriding both
# roots on the make command line; these defaults serve an in-place run.
A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/unittest/fixtures/inherit-tb-request

PROJECTNAME = itrTest
TB_TOP_MODULE = itrTop
HDL_TOP_MODULE = itrTop

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/itrProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
