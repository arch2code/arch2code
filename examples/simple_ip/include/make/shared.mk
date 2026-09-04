A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/simple_ip

PROJECTNAME = simple_ip
TB_TOP_MODULE = simple_ip
HDL_TOP_MODULE = simple_ip

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/project.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
