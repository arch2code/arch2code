#define SC_INCLUDE_DYNAMIC_PROCESSES
#include <iostream>
#include <systemc>

#include "apbDecode_testbench.h"

#if defined(VERILATOR) and (VM_TRACE_VCD == 1)
#include "verilated_vcd_sc.h"
#endif /* VERILATOR */

using namespace std;

int sc_main(int, char*[]) {

    cout << hex;

#if defined(VERILATOR) and (VM_TRACE_VCD == 1)
    Verilated::traceEverOn(true);
    VerilatedVcdSc* tfp = new VerilatedVcdSc;
#endif

    apbDecode_testbench *tb_i;

    tb_i = new apbDecode_testbench("tb_i");

    // Remove warning: variable ‘tc_i’ set but not used
    tb_i->dut_i->dump();

#if defined(VERILATOR) and (VM_TRACE_VCD == 1)
    sc_start(SC_ZERO_TIME);
    tb_i->dut_i->dut_hdl->trace(tfp, 3);
    tfp->open("waveform.vcd");
#endif

    sc_start(30, SC_US); // Timeout at 30us

    cout << "sc_main done at " << sc_time_stamp() << endl;

#if defined(VERILATOR) and (VM_TRACE_VCD == 1)
    tfp->close();
#endif

    return 0;
}
