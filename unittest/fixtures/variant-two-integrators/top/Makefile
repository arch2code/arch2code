include include/make/shared.mk

.PHONY : clean subprojects-newmodule subprojects-gen

clean::
	rm -rf $(A2C_SQLDB_DOTFILE) $(A2C_SQLDB_FILE) $(GEN_BUILD_DIR)

# The first integrator scaffolds, generates and cleans through its own targets,
# which in turn cover the leaf IP.
newmodule: subprojects-newmodule
subprojects-newmodule:
	$(MAKE) -C $(FIXTURE_ROOT)/mid newmodule

gen: subprojects-gen
subprojects-gen:
	$(MAKE) -C $(FIXTURE_ROOT)/mid gen

clean::
	$(MAKE) -C $(FIXTURE_ROOT)/mid clean
