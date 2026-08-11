A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/xprojParam/shared

PROJECTNAME = xpShared
TB_TOP_MODULE = xpSharedTop
HDL_TOP_MODULE = xpSharedTop

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/xpSharedProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
