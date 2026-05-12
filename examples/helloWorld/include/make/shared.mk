A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/helloWorld

PROJECTNAME = helloWorld
# helloWorld has no RTL or separate testbench; the top design block is `top`.
TB_TOP_MODULE = top
HDL_TOP_MODULE = top

#SKIP_GEN=1

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
