#ifndef VL_TRACER_H_
#define VL_TRACER_H_

#include "systemc.h"

#include "verilated_vcd_sc.h"

class vl_tracer: public sc_module {

public:
    VerilatedVcdSc* m_tfp;

    SC_HAS_PROCESS (vl_tracer);

    vl_tracer(sc_module_name modulename)
    {
        Verilated::traceEverOn(true);
        m_tfp = new VerilatedVcdSc;
        SC_THREAD(refresh_trace);
    }

    void open_trace() {
        m_tfp->open("simx.vcd");
        Verilated::scopesDump();
    }

    void close_trace() {
        m_tfp->flush();
        m_tfp->close();
    }

    void refresh_trace() {
        while (true) {
            wait(1, SC_NS);
            m_tfp->flush();
        }
    }

};

#endif /* VL_TRACER_H_ */
