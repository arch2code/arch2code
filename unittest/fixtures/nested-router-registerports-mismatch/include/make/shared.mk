# test_nested_router_registerports_mismatch.py builds a copy of this tree,
# overriding both roots on the make command line; these defaults serve an
# in-place run.
A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/unittest/fixtures/nested-router-registerports-mismatch

PROJECTNAME = nrpmTest
TB_TOP_MODULE = top
HDL_TOP_MODULE = top

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/nrpmProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
