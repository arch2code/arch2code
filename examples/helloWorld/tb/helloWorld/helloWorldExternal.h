#ifndef HELLOWORLD_EXTERNAL_H
#define HELLOWORLD_EXTERNAL_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=helloWorld
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "helloWorldBase.h"
#include "endOfTest.h"

//contained instances forward class declaration
class consumerBase;
class producerBase;

class helloWorldExternal: public sc_module, public helloWorldInverted {

    logBlock log_;

public:

    std::shared_ptr<producerBase> uProducer;
    std::shared_ptr<consumerBase> uConsumer;

    SC_HAS_PROCESS (helloWorldExternal);

    helloWorldExternal(sc_module_name modulename);

    // Ready Valid Test interface
    rdy_vld_channel< data_st > test_rdy_vld;
    // Req Ack Test interface
    req_ack_channel< data_st, data_st > test_req_ack;
    // Valid Ack Test interface
    push_ack_channel< data_st > test_push_ack;
    // Ready Ack Test interface
    pop_ack_channel< data_st > test_pop_ack;

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

// GENERATED_CODE_END
};

#endif /* HELLOWORLD_EXTERNAL_H */
