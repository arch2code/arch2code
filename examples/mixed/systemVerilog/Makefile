PROJECTNAME = mixed
REPO_ROOT = $(shell git rev-parse --show-toplevel)

DB_FILE = ../$(PROJECTNAME).db
DOT_DB_FILE = ../.$(PROJECTNAME).db
SV_COM = $(REPO_ROOT)/common/systemVerilog
PROJECT_DIRECTORY = $(REPO_ROOT)/examples/$(PROJECTNAME)
SV_DIR = $(PROJECT_DIRECTORY)/systemVerilog
DOT_GEN_FILE = $(SV_DIR)/.gen_file
LINT_INSTANCES = $(SV_DIR)/instancesList.yaml
SV_GEN_FILES = $(shell find $(SV_DIR) -type f -name '*.sv')
SV_FILES = $(shell find $(SV_DIR) -type f -name '*.sv' | grep -v ".*_package.sv")

all: $(DOT_DB_FILE)
.PHONY: clean $(DOT_DB_FILE) lint

# && touch after the build command only touches the dot file if the previous command is succesful
$(DOT_DB_FILE): 
	make -C ../arch && touch $@

.PHONY: init-packages
# initializes package files and creates the package.f file that is used during lint
init-packages: $(DOT_DB_FILE)
	$(REPO_ROOT)/arch2code.py -r --db $(DB_FILE) --initialSystemVerilogPackagesGenerator --moduledir $(SV_DIR)

$(DOT_GEN_FILE): $(DOT_DB_FILE)
	for i in $(SV_GEN_FILES); do $(REPO_ROOT)/arch2code.py --db $(DB_FILE) -r -sv --instances $(LINT_INSTANCES) --file $$i; done
	touch $@

lint: $(DOT_GEN_FILE)
	verilator --lint-only -sv $(SV_COM)/flops.sv -f package.f $(SV_FILES) --top-module top -y $(SV_COM)

clean:
	$(RM) $(DB_FILE) $(DOT_DB_FILE) $(DOT_GEN_FILE)
