# Verilator whole-design build entry: run via `make -C <build>/vl -f <this> vlwrap
# REPO_ROOT=<example root>`. Pulls the example's config + manifest, then the
# shared verilation rules. Wrapper sources are node-scoped; outputs land here.
include $(REPO_ROOT)/include/make/shared.mk
include $(A2C_ROOT)/include/make/a2c-vl-wrap.mk
