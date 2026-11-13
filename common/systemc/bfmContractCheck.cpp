#include "bfmContractCheck.h"

// DPI import of the UVM testbench module, which polls it once a clock: the
// next queued BFM contract break, or "" when none is waiting. Other flows
// link it without calling it. The string lives in uvmBreaks; SystemVerilog
// copies it before SystemC can queue another.
extern "C" const char *a2c_bfm_contract_break(void)
{
    if (bfmContractCheck::uvmTaken == bfmContractCheck::uvmBreaks.size()) {
        return "";
    }
    return bfmContractCheck::uvmBreaks[bfmContractCheck::uvmTaken++].c_str();
}
