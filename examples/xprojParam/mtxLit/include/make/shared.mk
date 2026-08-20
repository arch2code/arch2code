A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/xprojParam/mtxLit

PROJECTNAME = xpMtxLit
TB_TOP_MODULE = xpMtxLitTop
HDL_TOP_MODULE = xpMtxLitTop

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/xpMtxLitProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
