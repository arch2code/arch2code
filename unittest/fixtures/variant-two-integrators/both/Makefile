include include/make/shared.mk

.PHONY : clean subprojects-newmodule subprojects-gen

clean::
	rm -rf $(A2C_SQLDB_DOTFILE) $(A2C_SQLDB_FILE) $(GEN_BUILD_DIR)

# The second integrator's project scaffolds, generates and cleans through its
# own targets, which in turn cover the first integrator and the leaf IP.
newmodule: subprojects-newmodule
subprojects-newmodule:
	$(MAKE) -C $(FIXTURE_ROOT)/top newmodule

gen: subprojects-gen
subprojects-gen:
	$(MAKE) -C $(FIXTURE_ROOT)/top gen

clean::
	$(MAKE) -C $(FIXTURE_ROOT)/top clean
