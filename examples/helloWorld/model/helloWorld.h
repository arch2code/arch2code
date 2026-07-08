#ifndef HELLOWORLD_H
#define HELLOWORLD_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"


// GENERATED_CODE_PARAM --block=helloWorld
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
import helloWorld.base;
#include "pop_ack_channel.h"
#include "push_ack_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"
import helloWorld_tb;
using namespace helloWorld_tb_ns;
//contained instances base module imports
import producer.base;
import consumer.base;

SC_MODULE(helloWorld), public blockBase, public helloWorldBase
{
private:

public:
    // channels
    // Ready Valid Test interface
    rdy_vld_channel< data_st > test_rdy_vld;
    // Req Ack Test interface
    req_ack_channel< data_st, data_st > test_req_ack;
    // Valid Ack Test interface
    push_ack_channel< data_st > test_push_ack;
    // Ready Ack Test interface
    pop_ack_channel< data_st > test_pop_ack;

    //instances contained in block
    std::shared_ptr<producerBase> uProducer;
    std::shared_ptr<consumerBase> uConsumer;

    helloWorld(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~helloWorld() override = default;

    // GENERATED_CODE_END
    // block implementation members
    std::shared_ptr<tracker<simpleString>> pingPong;
    void doneTest(void);

};

#endif //HELLOWORLD_H

