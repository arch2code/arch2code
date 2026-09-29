A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/xprojParam/inhLayoutBad

PROJECTNAME = xpInhLayoutBad
TB_TOP_MODULE = xpInhLayoutBadTop
HDL_TOP_MODULE = xpInhLayoutBadTop

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/xpInhLayoutBadProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
