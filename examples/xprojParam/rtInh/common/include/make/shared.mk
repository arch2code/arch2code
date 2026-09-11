A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/xprojParam/rtInh/common

PROJECTNAME = common
# Definitions-only project: no design top or HDL top. These are required by
# a2c-common.mk but are unused because this project only builds db/gen (no run).
TB_TOP_MODULE = common
HDL_TOP_MODULE = common

# This project's entry YAML is commonProject.yaml (not the default project.yaml).
A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/commonProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
