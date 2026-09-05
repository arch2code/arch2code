include include/make/shared.mk

.PHONY : clean subprojects-newmodule subprojects-gen

clean::
	rm -rf $(A2C_SQLDB_DOTFILE) $(A2C_SQLDB_FILE) $(GEN_BUILD_DIR)

# The leaf IP scaffolds, generates and cleans through its own targets.
newmodule: subprojects-newmodule
subprojects-newmodule:
	$(MAKE) -C $(FIXTURE_ROOT)/ipLeaf newmodule

gen: subprojects-gen
subprojects-gen:
	$(MAKE) -C $(FIXTURE_ROOT)/ipLeaf gen

clean::
	$(MAKE) -C $(FIXTURE_ROOT)/ipLeaf clean
