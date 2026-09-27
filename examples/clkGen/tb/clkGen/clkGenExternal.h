#ifndef CLKGEN_EXTERNAL_H
#define CLKGEN_EXTERNAL_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=clkGen
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "instanceFactory.h"
import clkGen.base;
import clkGen_clkConsumer.base;
import clkGen_clkDivider.base;
import clkGen_rstSync.base;

class clkGenExternal: public sc_module, public clkGenInverted {

    logBlock log_;

public:

    std::shared_ptr<clkDividerBase> uDivider;
    std::shared_ptr<rstSyncBase> uRstSync;
    std::shared_ptr<clkConsumerBase> uConsumer;

    SC_HAS_PROCESS (clkGenExternal);

    clkGenExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

// GENERATED_CODE_END

    // clkGen has no boundary ports for the External to drive: the divider
    // free-runs off clkRef/rstRef_n and the consumer free-runs off the
    // divided clock it is handed. The External owns the run window and, when
    // a verilated divider is present, checks the clkDiv it produces. Models
    // are unclocked, so a model-only run has no clkDiv to check. The
    // synchronised reset and the consumer are internal to clkGen's RTL and
    // are checked there.
    void stimulusThread(void);

private:
    sc_signal_in_if<bool> *findClkDiv(void);
    void checkClkDiv(sc_signal_in_if<bool> &clkDiv);

    endOfTest eot_{true};   // registers this thread as a voter

};

#endif /* CLKGEN_EXTERNAL_H */
