PROJECT_NAME = apbDecode

REPO_ROOT = $(shell git rev-parse --show-toplevel)
PROJECT_ROOT = $(REPO_ROOT)/examples/$(PROJECT_NAME)

include $(REPO_ROOT)/examples/include/shared.mk

SV_COM = $(REPO_ROOT)/common/systemVerilog
SV_DIR = $(PROJECT_ROOT)/systemVerilog
DOT_GEN_FILE = $(SV_DIR)/.gen_file
SV_GEN_FILES = $(shell find $(SV_DIR) -type f -name '*.sv')

.PHONY: all clean lint init-packages

all: db

# initializes package files and creates the package.f file that is used during lint
init-packages: $(DOT_DB_FILE)
	$(REPO_ROOT)/arch2code.py -r --db $(DB_FILE) --initialSystemVerilogPackagesGenerator --moduledir $(SV_DIR)

$(DOT_GEN_FILE): $(DOT_DB_FILE)
	for i in $(SV_GEN_FILES); do $(REPO_ROOT)/arch2code.py --db $(DB_FILE) -r -sv --file $$i; done
	touch $@

all : lint

gen: $(DOT_GEN_FILE)

lint: gen
	verilator --lint-only -F $(SV_COM)/a2c.f -f package.f -f $(PROJECT_NAME).f --top-module top

clean: db-clean
	$(RM) $(DOT_GEN_FILE)
