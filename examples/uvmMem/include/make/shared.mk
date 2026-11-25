A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/uvmMem

PROJECTNAME = uvmMem
TB_TOP_MODULE = uvmMem_tb
HDL_TOP_MODULE = uvmMem

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/uvmMemProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
