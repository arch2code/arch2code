A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/uvmReuse

PROJECTNAME = uvmReuse
TB_TOP_MODULE = uvmReuse_tb
HDL_TOP_MODULE = uvmReuseChain

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/uvmReuseProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
