A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/hierVlDemo

PROJECTNAME = hierVlDemo
TB_TOP_MODULE = axi4s_tb
HDL_TOP_MODULE = hierVlDemo

#SKIP_GEN=1

# # Anchor the actual project root to the shared makefile path location in the repository
# # This allows the project to be built from any directory without needing to adjust paths.
# prj_shared_mkfile_path := $(strip $(subst $(REPO_ROOT),, $(subst /include/make/shared.mk,, $(abspath $(lastword $(MAKEFILE_LIST))))))

# ifeq ($(prj_shared_mkfile_path),)
# PROJECT_ROOT := $(REPO_ROOT)
# else
# PROJECT_ROOT := $(REPO_ROOT)/$(prj_shared_mkfile_path)
# endif

# $(info "Using shared makefile from: $(PROJECT_ROOT)")

A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/hierVlDemoProject.yaml

# User-hosted generated-region file: arch2code injects the address defines (via
# the includes template) into this user-authored host header. Not fileMap-
# scaffolded, so it rides the EXTRA_ generation seam.
EXTRA_SC_GEN_FILES = $(REPO_ROOT)/fw/axi4sRegAddresses.h

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
