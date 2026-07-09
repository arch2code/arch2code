A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/ip_test/ip

PROJECTNAME = ip
TB_TOP_MODULE = ip
HDL_TOP_MODULE = ip

# This project's entry YAML is ipProject.yaml (not the default project.yaml).
A2C_PRJ_YAML = $(REPO_ROOT)/arch/yaml/ipProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
