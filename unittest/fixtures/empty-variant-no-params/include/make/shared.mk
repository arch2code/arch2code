# test_error_variant_on_params_less_block.py builds a copy of this tree,
# overriding both roots on the make command line; these defaults serve an
# in-place run.
A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/unittest/fixtures/empty-variant-no-params

PROJECTNAME = epvTest
TB_TOP_MODULE = epvTop
HDL_TOP_MODULE = epvTop

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/epvProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
