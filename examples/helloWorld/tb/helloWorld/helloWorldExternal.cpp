#include "helloWorldExternal.h"
#include "workerThread.h"

// GENERATED_CODE_PARAM --block=helloWorld

// GENERATED_CODE_BEGIN --template=tbExternal --section=init
#include "producerBase.h"
#include "consumerBase.h"

helloWorldExternal::helloWorldExternal(sc_module_name modulename) :
    helloWorldInverted("Chnl"),
    log_(name())

   ,uProducer(std::dynamic_pointer_cast<producerBase>( instanceFactory::createInstance(name(), "uProducer", "producer", "")))
   ,uConsumer(std::dynamic_pointer_cast<consumerBase>( instanceFactory::createInstance(name(), "uConsumer", "consumer", "")))
   ,test_rdy_vld("test_rdy_vld", "uProducer")
   ,test_req_ack("test_req_ack", "uProducer")
   ,test_push_ack("test_push_ack", "uProducer")
   ,test_pop_ack("test_pop_ack", "uProducer")
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{
    // instance to instance connections via channel
    uProducer->test_rdy_vld(test_rdy_vld);
    uConsumer->test_rdy_vld(test_rdy_vld);
    uProducer->test_req_ack(test_req_ack);
    uConsumer->test_req_ack(test_req_ack);
    uProducer->test_push_ack(test_push_ack);
    uConsumer->test_push_ack(test_push_ack);
    uProducer->test_pop_ack(test_pop_ack);
    uConsumer->test_pop_ack(test_pop_ack);

    SC_THREAD(eotThread);
// GENERATED_CODE_END
}
