#ifndef CONSUMER_HDL_SC_WRAPPER_H_
#define CONSUMER_HDL_SC_WRAPPER_H_

#include "systemc.h"

#include "instanceFactory.h"

#include "rdy_vld_bfm.h"
#include "rdy_vld_burst_bfm.h"
#include "req_ack_bfm.h"
#include "pop_ack_bfm.h"
#include "vld_ack_bfm.h"
#include "start_done_bfm.h"
#include "apb_bfm.h"

// GENERATED_CODE_PARAM --block=consumer

#include "consumerBase.h"

// Verilated RTL top (SystemC)
#if !defined(VERILATOR) && defined(VCS)
#include "consumer_hdl_sv_wrapper.h"
#else
#include "Vconsumer_hdl_sv_wrapper.h"
#endif

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class
// GENERATED_CODE_END

    // Callback executed at the end of module constructor
    void end_ctor_init() {
        // Register synchLock,...
    }

};

#endif // CONSUMER_HDL_SC_WRAPPER_H_
