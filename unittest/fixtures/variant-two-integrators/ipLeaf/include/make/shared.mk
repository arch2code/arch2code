# test_variant_two_integrators.py builds a copy of this tree and overrides
# A2C_ROOT and FIXTURE_ROOT on the make command line, so both reach the
# sub-project makes; these defaults serve an in-place run.
A2C_ROOT = $(shell git rev-parse --show-toplevel)
FIXTURE_ROOT = $(A2C_ROOT)/unittest/fixtures/variant-two-integrators
REPO_ROOT = $(FIXTURE_ROOT)/ipLeaf

PROJECTNAME = xviLeaf
# Required by a2c-common.mk and unused: this project has no design top, it only
# builds db/gen.
TB_TOP_MODULE = xviLeaf
HDL_TOP_MODULE = xviLeaf

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/xviLeafProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
