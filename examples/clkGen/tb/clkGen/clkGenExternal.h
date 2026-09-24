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
    // divided clock it is handed, neither one checked by an assertion here.
    // What the External owns is the run window: it must outlast a verilated
    // DUT's reset release (a few clkRef edges) and several clkDiv edges
    // beyond that, across every --vlInst configuration make -j8
    // clk-gen exercises.
    void stimulusThread(void);

private:
    endOfTest eot_{true};   // registers this thread as a voter

};

#endif /* CLKGEN_EXTERNAL_H */
