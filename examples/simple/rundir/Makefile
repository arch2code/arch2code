REPO_ROOT = $(shell git rev-parse --show-toplevel)/examples/simple
include $(REPO_ROOT)/include/make/shared.mk

# Include External dependencies in compilation
EXTRA_CPP_SRC      =
EXTRA_CPP_INCLUDES =
EXTRA_LD_FLAGS     =

# Include generated files with names matching '*Includes*.cpp' in SC_GEN_FILES.
EXTRA_O3_CPP_SRC   = $(filter %Includes.cpp %IncludesFW.cpp, $(SC_GEN_FILES))

include $(A2C_ROOT)/include/make/a2c-systemc.mk

.PHONY : run run-vl run-vl-producer run-vl-consumer

run: $(BIN_DIR)/$(BIN)
ifndef VL_DUT
	$(BIN_DIR)/$(BIN) $(PROJECTNAME)
else
	$(BIN_DIR)/$(BIN) $(PROJECTNAME) --vlInst $(HDL_TOP_MODULE)
endif

# Partial cosim: verilate one leaf and leave the other as a model, so the tag
# push_ack handshake crosses the SC/RTL boundary and the surviving side checks
# the verilated one. u_producer verilated proves RTL -> model (the model
# consumer's Q_ASSERT is the checker); u_consumer verilated proves model -> RTL
# (the RTL consumer's qAssertFatal is the checker).
#
# There is deliberately no whole-DUT target here. --vlInst simple replaces
# u_simple, whose doneTest thread is the run's only end-of-test voter, leaving
# nothing to check the RTL. The watchdog now ends that run rather than letting it
# hang, but a target that can only report its own emptiness is not worth having.
run-vl:
	$(MAKE) all VL_DUT=1
	$(MAKE) run-vl-producer VL_DUT=1
	$(MAKE) run-vl-consumer VL_DUT=1

run-vl-producer: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(PROJECTNAME) --vlInst $(HDL_TOP_MODULE).u_producer

run-vl-consumer: $(BIN_DIR)/$(BIN)
	$(BIN_DIR)/$(BIN) $(PROJECTNAME) --vlInst $(HDL_TOP_MODULE).u_consumer
