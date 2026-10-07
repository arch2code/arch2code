A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/twoClk/ip

PROJECTNAME = twoClkIp
# Ported-block-only project: no design top and no HDL top of its own. Both are
# required by a2c-common.mk but are unused here because this project only builds
# db/gen (no simulation).
TB_TOP_MODULE = twoClkIpSrc
HDL_TOP_MODULE = twoClkIpSrc

# This project's entry YAML is twoClkIpProject.yaml (not the default project.yaml).
A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/twoClkIpProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
