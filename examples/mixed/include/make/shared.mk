A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/examples/mixed

PROJECTNAME = mixed
TB_TOP_MODULE = mixed
HDL_TOP_MODULE = mixed

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

# User-hosted generated-region files: arch2code injects generated sections into
# these user-authored hosts - the address defines (includes template) and the
# encoder C++/SV units (encoder templates). Not fileMap-scaffolded, so they ride
# the EXTRA_ generation seam.
EXTRA_SC_GEN_FILES = $(REPO_ROOT)/model/regAddresses.h $(REPO_ROOT)/model/mixedEncoders.h
EXTRA_SV_GEN_FILES = $(REPO_ROOT)/rtl/mixedEncoder_package.sv

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk

