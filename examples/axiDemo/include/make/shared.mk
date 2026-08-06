A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/axiDemo

PROJECTNAME = axiDemo
TB_TOP_MODULE = axiDemo
HDL_TOP_MODULE = axiDemo

#SKIP_GEN=1

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
