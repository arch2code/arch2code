// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <memory>
#include "instanceFactory.h"
#include "endOfTest.h"
#include "testController.h"

// GENERATED_CODE_PARAM --block=helloWorld
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "helloWorld.h"
import producer.base;
import consumer.base;
SC_HAS_PROCESS(helloWorld);

// === Block factory registration (helloWorld) ===
void register_helloWorld_variants() {
    instanceFactory::registerBlock("helloWorld_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<helloWorld>(blockName, variant, bbMode)); }, "", "helloWorld");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _helloWorld_registered = (register_helloWorld_variants(), 0);
} // namespace
// === End block factory registration ===

helloWorld::helloWorld(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("helloWorld", name(), bbMode)
        ,helloWorldBase(name(), variant)
        ,test_rdy_vld("consumer_test_rdy_vld", "producer")
        ,test_req_ack("consumer_test_req_ack", "producer")
        ,test_push_ack("consumer_test_push_ack", "producer")
        ,test_pop_ack("consumer_test_pop_ack", "producer")
        ,uProducer(std::dynamic_pointer_cast<producerBase>(instanceFactory::createInstance(name(), "uProducer", "producer", "", "helloWorld")))
        ,uConsumer(std::dynamic_pointer_cast<consumerBase>(instanceFactory::createInstance(name(), "uConsumer", "consumer", "", "helloWorld")))
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
    SC_THREAD(doneTest);
}

// End-of-test bridge: the model is self-driving via testController. Wait for all
// registered tests to complete, then vote end-of-test so helloWorldExternal::eotThread
// can sc_stop() the simulation.
void helloWorld::doneTest(void)
{
    endOfTest eot;
    eot.registerVoter();
    testController::GetInstance().wait_all_tests_complete();
    eot.setEndOfTest(true);
}
