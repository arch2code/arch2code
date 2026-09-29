A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/xprojParam/inhVar

PROJECTNAME = xpInhVar
TB_TOP_MODULE = xpInhTop
HDL_TOP_MODULE = xpInhTop

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/xpInhVarProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
