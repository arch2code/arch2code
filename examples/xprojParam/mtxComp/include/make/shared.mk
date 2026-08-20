A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/xprojParam/mtxComp

PROJECTNAME = xpMtxComp
TB_TOP_MODULE = xpMtxCompTop
HDL_TOP_MODULE = xpMtxCompTop

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/xpMtxCompProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
