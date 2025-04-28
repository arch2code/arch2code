#ifndef PIPE_HDL_SC_WRAPPER_H_
#define PIPE_HDL_SC_WRAPPER_H_

#include "systemc.h"

#include "instanceFactory.h"

#include "rdy_vld_bfm.h"
#include "rdy_vld_burst_bfm.h"
#include "req_ack_bfm.h"
#include "pop_ack_bfm.h"
#include "vld_ack_bfm.h"
#include "start_done_bfm.h"
#include "apb_bfm.h"

// GENERATED_CODE_PARAM --block=pipe

#include "pipeBase.h"

// Verilated RTL top (SystemC)
#if !defined(VERILATOR) && defined(VCS)
#include "pipe_hdl_sv_wrapper.h"
#else
#include "Vpipe_hdl_sv_wrapper.h"
#endif

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class
// GENERATED_CODE_END

    // Callback executed at the end of module constructor
    void end_ctor_init() {
        // Register synchLock,...
    }

};

#endif // PIPE_HDL_SC_WRAPPER_H_
