A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/uvmRegs

PROJECTNAME = uvmRegs
TB_TOP_MODULE = uvmRegs_tb
HDL_TOP_MODULE = uvmRegs

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/uvmRegsProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
