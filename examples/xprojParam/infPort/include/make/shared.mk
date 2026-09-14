A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/xprojParam/infPort

PROJECTNAME = xpInfPort
TB_TOP_MODULE = xpInfTop
HDL_TOP_MODULE = xpInfTop

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/xpInfPortProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
