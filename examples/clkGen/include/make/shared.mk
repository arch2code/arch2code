A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/clkGen

PROJECTNAME = clkGen
# The DUT block carries hasTb and is also the verilated top, so both names are
# the same block here.
TB_TOP_MODULE = clkGen
HDL_TOP_MODULE = clkGen

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/project.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
