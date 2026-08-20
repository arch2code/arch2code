A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/xprojParam/twoCtx

PROJECTNAME = xpTwoCtx
TB_TOP_MODULE = xpTwoCtxTop
HDL_TOP_MODULE = xpTwoCtxTop

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/xpTwoCtxProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
