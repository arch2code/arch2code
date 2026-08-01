//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=helloWorld --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "pop_ack_channel.h"
#include "push_ack_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"
// GENERATED_CODE_END
#include <memory>
#include "instanceFactory.h"
#include "endOfTest.h"
#include "testController.h"
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module helloWorld.block;
import helloWorld.base;
import helloWorld_tb;
import helloWorld_producer.base;
import helloWorld_consumer.base;
using namespace helloWorld_tb_ns;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
export SC_MODULE(helloWorld), public blockBase, public helloWorldBase
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

// GENERATED_CODE_BEGIN --template=constructor --section=init
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
};

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

