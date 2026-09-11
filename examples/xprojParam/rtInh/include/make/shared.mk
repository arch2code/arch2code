A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/xprojParam/rtInh

PROJECTNAME = xpRtInh
TB_TOP_MODULE = xpRtInhTop
HDL_TOP_MODULE = xpRtInhTop

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/project.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
