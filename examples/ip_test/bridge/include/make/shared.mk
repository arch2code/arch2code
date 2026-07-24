A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/ip_test/bridge

PROJECTNAME = ipBridge
TB_TOP_MODULE = bridgeStdTop
HDL_TOP_MODULE = bridgeStdTop

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/ipBridgeProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
