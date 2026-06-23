A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/helloWorld

PROJECTNAME = helloWorld
TB_TOP_MODULE = helloWorld_tb
HDL_TOP_MODULE = helloWorld

#SKIP_GEN=1

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
