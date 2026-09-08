# test_block_param_eval_backing.py builds a copy of this tree, overriding both
# roots on the make command line; these defaults serve an in-place run.
A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/unittest/fixtures/block-param-eval-backing

PROJECTNAME = bpeTest
TB_TOP_MODULE = bpeTop
HDL_TOP_MODULE = bpeTop

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/bpeProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
