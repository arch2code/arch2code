A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/axiSocketMaster

PROJECTNAME = axiSocketMaster
TB_TOP_MODULE = axiSocket
HDL_TOP_MODULE = axiSocket

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
