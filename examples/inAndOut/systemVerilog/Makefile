REPO_ROOT = $(shell git rev-parse --show-toplevel)
PROJECTNAME = inAndOut
DB_FILE = ../$(PROJECTNAME).db
DOT_DB_FILE = ../.$(PROJECTNAME).db
SV_COM = $(REPO_ROOT)/common/systemVerilog
LINT_INSTANCES = instancesList.yaml
VL_OBJ_DIR = obj_dir

db: $(DOT_DB_FILE)

all: $(DOT_DB_FILE)
.PHONY: clean lint sim

# && touch after the build command only touches the dot file if the previous command is succesful
$(DOT_DB_FILE):
	make -C ../arch

package.f: $(DOT_DB_FILE)
	$(REPO_ROOT)/arch2code.py --db $(DB_FILE) -r -ibt | awk '{print $$6}' | awk '!seen[$$0]++' | awk '{print "-sv "$$0"_package.sv"}' > $@

lint: $(DOT_DB_FILE)
	$(REPO_ROOT)/arch2code.py --db $(DB_FILE) -r -sv --instances $(LINT_INSTANCES) --file inAndOut_package.sv
	$(REPO_ROOT)/arch2code.py --db $(DB_FILE) -r -sv --instances $(LINT_INSTANCES) --file inAndOut.sv
	verilator --lint-only -sv inAndOut_package.sv -sv inAndOut.sv --top-module inAndOut -y . -y $(SV_COM)

CPP_SRCS = simInAndOut/sc_main.cpp simInAndOut/inAndOutIncludes.cpp
CPP_SRCS += $(wildcard $(REPO_ROOT)/common/systemc/*.cpp)

sim: $(DOT_DB_FILE)
	$(REPO_ROOT)/arch2code.py --db $(DB_FILE) -r -sv --instances $(LINT_INSTANCES) --file simInAndOut/inAndOut_hdl_sv_wrapper.sv
	$(REPO_ROOT)/arch2code.py --db $(DB_FILE) -r -sc --instances $(LINT_INSTANCES) --file simInAndOut/inAndOut_hdl_sc_wrapper.h
	$(REPO_ROOT)/arch2code.py --db $(DB_FILE) -r -sc --instances $(LINT_INSTANCES) --file simInAndOut/inAndOutIncludes.h
	$(REPO_ROOT)/arch2code.py --db $(DB_FILE) -r -sc --instances $(LINT_INSTANCES) --file simInAndOut/inAndOutIncludes.cpp
	$(REPO_ROOT)/arch2code.py --db $(DB_FILE) -r -sc --instances $(LINT_INSTANCES) --file simInAndOut/inAndOut_base.h
	verilator --Mdir $(VL_OBJ_DIR) -sc -sv --trace --trace-structs --trace-params --pins-bv 2 --no-timing --build -Wno-fatal -CFLAGS "-std=c++17 -I$(REPO_ROOT)/common/systemc  -I$(REPO_ROOT)/common/systemc/include/fmt -DVM_TRACE_VCD=1 -DVERILATOR" -LDFLAGS "-lfmt -L$(LD_BOOST) -lboost_system -lboost_program_options" $(CPP_SRCS) --sv inAndOut_package.sv --sv inAndOut.sv --sv simInAndOut/inAndOut_hdl_sv_wrapper.sv --top inAndOut_hdl_sv_wrapper -y $(SV_COM) -exe -o simx
	$(VL_OBJ_DIR)/simx


clean:
	rm -f $(DOT_DB_FILE)
	rm -f $(DB_FILE)
	rm -rf $(VL_OBJ_DIR) waveform.vcd
