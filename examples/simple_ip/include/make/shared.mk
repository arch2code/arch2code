A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/simple_ip

PROJECTNAME = simple_ip
TB_TOP_MODULE = simple_ip
HDL_TOP_MODULE = simple_ip

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/project.yaml

# User-hosted generated-region file: arch2code injects the address defines (via
# the includes template) into this user-authored host header. Not fileMap-
# scaffolded, so it rides the EXTRA_ generation seam.
EXTRA_SC_GEN_FILES = $(REPO_ROOT)/model/regAddresses.h

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
