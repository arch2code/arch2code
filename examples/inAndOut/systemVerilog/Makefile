REPO_ROOT = $(shell git rev-parse --show-toplevel)
PROJECTNAME = inAndOut
DB_FILE = ../$(PROJECTNAME).db
DOT_DB_FILE = ../.$(PROJECTNAME).db
SV_COM = $(REPO_ROOT)/common/systemVerilog

db: $(DOT_DB_FILE)

all: $(DOT_DB_FILE)
.PHONY: clean lint

# && touch after the build command only touches the dot file if the previous command is succesful
$(DOT_DB_FILE):
	make -C ../arch

package.f: $(DOT_DB_FILE)
	$(REPO_ROOT)/arch2code.py --db $(DB_FILE) -r -ibt | awk '{print $$6}' | awk '!seen[$$0]++' | awk '{print "-sv "$$0"_package.sv"}' > $@

lint: $(DOT_DB_FILE)
	$(REPO_ROOT)/arch2code.py --db $(DB_FILE) -r -sv --file inAndOut_package.sv
	$(REPO_ROOT)/arch2code.py --db $(DB_FILE) -r -sv --file inAndOut.sv
	verilator --lint-only -sv -F $(SV_COM)/a2c.f inAndOut_package.sv -sv inAndOut.sv --top-module inAndOut -y . -y $(SV_COM)

clean:
	rm -f $(DOT_DB_FILE)
	rm -f $(DB_FILE)
