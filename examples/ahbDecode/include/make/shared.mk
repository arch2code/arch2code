A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/ahbDecode

PROJECTNAME = ahbDecode
TB_TOP_MODULE = ahbSoc
HDL_TOP_MODULE = ahbSoc

#SKIP_GEN=1

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
