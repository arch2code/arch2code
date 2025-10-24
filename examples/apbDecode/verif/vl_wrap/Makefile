PROJECT_NAME = apbDecode

REPO_ROOT = $(shell git rev-parse --show-toplevel)
PROJECT_ROOT = $(REPO_ROOT)/examples/$(PROJECT_NAME)

include $(REPO_ROOT)/examples/include/shared.mk

C_STD_VER=c++23

VERILATOR_OPTS = -sc -sv --trace --trace-structs --trace-params --pins-bv 2 --no-timing --build -Wno-fatal -j 4
VERILATOR_CFLAG_OPTS = '-std=$(C_STD_VER) -DSC_CPLUSPLUS=201703L'

CPP_SRCS = sc_main.cpp

GEN_SV_FILES = $(shell find . -name '*.sv' -exec grep -E -l 'GENERATED_CODE_BEGIN' {} +)
GEN_H_FILES = $(shell find . $(PROJECT_ROOT)/includes -name '*.h' -exec grep -E -l 'GENERATED_CODE_BEGIN' {} +)

h:
	echo $(GEN_SV_FILES)

$(GEN_SV_FILES) : $(DOT_DB_FILE) 
	$(REPO_ROOT)/arch2code.py --readonly --db $(DB_FILE) -sv --file $@
$(GEN_H_FILES) : $(DOT_DB_FILE) 
	$(REPO_ROOT)/arch2code.py --readonly --db $(DB_FILE) -sc --file $@

gen: $(GEN_SV_FILES) $(GEN_H_FILES)

VL_OBJ_FILES = $(subst ./,obj_dir/V, $(patsubst %.sv, %.o, $(GEN_SV_FILES)))

$(VL_OBJ_FILES): $(GEN_SV_FILES)
	verilator $(VERILATOR_OPTS) -CFLAGS $(VERILATOR_CFLAG_OPTS) $(CPP_SRCS) -F $(REPO_ROOT)/common/systemVerilog/a2c.f -F $(PROJECT_ROOT)/systemVerilog/package.f -F $(PROJECT_ROOT)/systemVerilog/$(PROJECT_NAME).f $(subst obj_dir/V,, $(patsubst %.o, %.sv, $@)) -top $(notdir $(subst obj_dir/V,, $(patsubst %.o,%, $@))) --exe


libvl_s_wrap.a: $(VL_OBJ_FILES)
	ar -rcs $@ obj_dir/verilated.o obj_dir/verilated_vcd_c.o obj_dir/verilated_threads.o obj_dir/V*_hdl_sv_wrapper*.o

all : gen libvl_s_wrap.a

clean: db-clean
	rm -rf libvl_s_wrap.a obj_dir/
