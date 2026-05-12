//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=helloWorld
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "helloWorld.h"
#include "producerBase.h"
#include "consumerBase.h"
SC_HAS_PROCESS(helloWorld);

helloWorld::registerBlock helloWorld::registerBlock_; //register the block with the factory

helloWorld::helloWorld(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("helloWorld", name(), bbMode)
        ,helloWorldBase(name(), variant)
        ,test_rdy_vld("consumer_test_rdy_vld", "producer")
        ,test_req_ack("consumer_test_req_ack", "producer")
        ,test_push_ack("consumer_test_push_ack", "producer")
        ,test_pop_ack("consumer_test_pop_ack", "producer")
        ,uProducer(std::dynamic_pointer_cast<producerBase>( instanceFactory::createInstance(name(), "uProducer", "producer", "")))
        ,uConsumer(std::dynamic_pointer_cast<consumerBase>( instanceFactory::createInstance(name(), "uConsumer", "consumer", "")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
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
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

