#ifndef DUT_EXTERNAL_H
#define DUT_EXTERNAL_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=xif_tb --excludeInst=uDut
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "instanceFactory.h"
import dut.base;
import sink.base;
import src.base;
import xif;
using namespace xif_ns;
#include "xifVariantConfig.h"
#include "push_ack_port_thunker.h"
#include "endOfTest.h"

class dutExternal: public sc_module, public dutInverted<xifDefaultConfig> {

    logBlock log_;

public:

    std::shared_ptr<srcBase<xifDefaultConfig>> uSrc;
    std::shared_ptr<sinkBase<xifDefaultConfig>> uSink;

    SC_HAS_PROCESS (dutExternal);

    dutExternal(sc_module_name modulename);

    // cross-interface thunkers
    push_ack_port_thunker<streamSt<xifDefaultConfig>, streamBndrySt> thunker_out_uSrc;
    push_ack_port_thunker<streamSt<xifDefaultConfig>, streamBndrySt> thunker_streamOut_uSink;

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

// GENERATED_CODE_END
};

#endif /* DUT_EXTERNAL_H */
