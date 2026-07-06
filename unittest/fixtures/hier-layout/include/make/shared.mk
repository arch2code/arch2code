# Build harness for the green-field hierarchical-layout fixture
# (plan-decomp-functional-layout.md T2a.3). User-owned, committed: it is the
# project's build config, living at the project root under include/ (Q-L3
# amended: build config and rundir/ are user-owned entry points that stay at the
# root; only generated orphans move under prj/). The structural-golden test
# (test_layout_hierarchical.py) generates from the node dirs only, so this
# root-level harness never reaches the generated-only listing.
A2C_ROOT = $(shell git rev-parse --show-toplevel)
REPO_ROOT = $(A2C_ROOT)/unittest/fixtures/hier-layout

PROJECTNAME = hier
TB_TOP_MODULE = hier_tb
HDL_TOP_MODULE = core

# Hierarchical layout puts the project file in the prj/ container, not the
# functional arch/yaml/ root; re-point the build *input* (set before
# a2c-common.mk's `?=` default).
A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/hierProject.yaml

-include $(A2C_ROOT)/pro/include/make/a2cPro.mk
include $(A2C_ROOT)/include/make/a2c-common.mk
