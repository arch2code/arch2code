A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/axi4sDemo

PROJECTNAME = axi4sDemo
TB_TOP_MODULE = axi4s_tb
HDL_TOP_MODULE = axi4sDemo

SKIP_GEN=1

# # Anchor the actual project root to the shared makefile path location in the repository
# # This allows the project to be built from any directory without needing to adjust paths.
# prj_shared_mkfile_path := $(strip $(subst $(REPO_ROOT),, $(subst /include/make/shared.mk,, $(abspath $(lastword $(MAKEFILE_LIST))))))

# ifeq ($(prj_shared_mkfile_path),)
# PROJECT_ROOT := $(REPO_ROOT)
# else
# PROJECT_ROOT := $(REPO_ROOT)/$(prj_shared_mkfile_path)
# endif

# $(info "Using shared makefile from: $(PROJECT_ROOT)")

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
