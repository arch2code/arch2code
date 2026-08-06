A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/apbDecode

PROJECTNAME = apbDecode
TB_TOP_MODULE = someRapper
HDL_TOP_MODULE = someRapper

#SKIP_GEN=1

# User-hosted generated-region file: arch2code injects the address defines (via
# the includes template) into this user-authored host header. Not fileMap-
# scaffolded, so it rides the EXTRA_ generation seam.
EXTRA_SC_GEN_FILES = $(REPO_ROOT)/model/regAddresses.h

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
