A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/xprojParam/cppLeaf

PROJECTNAME = xpCppLeaf
# Definitions-and-block project with no design top: these are required by
# a2c-common.mk but unused, since this project only builds db/gen (no run).
TB_TOP_MODULE = xpCppLeaf
HDL_TOP_MODULE = xpCppLeaf

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/xpCppLeafProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
