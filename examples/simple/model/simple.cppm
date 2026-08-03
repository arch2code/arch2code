//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=simple --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "push_ack_channel.h"
// GENERATED_CODE_END
#include "testController.h"
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module simple.block;
import simple.base;
import simple;
import simple_producer.base;
import simple_consumer.base;
// GENERATED_CODE_END
// user imports here
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace simple_ns;
export SC_MODULE(simple), public blockBase, public simpleBase
{
private:

public:
    // channels
    // tag interface
    push_ack_channel< tag_st > tag0;
    // tag interface
    push_ack_channel< tag_st > tag1;

    //instances contained in block
    std::shared_ptr<producerBase> u_producer;
    std::shared_ptr<consumerBase> u_consumer;

    simple(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~simple() override = default;

    // GENERATED_CODE_END
    // block implementation members

    void doneTest(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(simple);

// === Block factory registration (simple) ===
void register_simple_variants() {
    instanceFactory::registerBlock("simple_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<simple>(blockName, variant, bbMode)); }, "", "simple");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _simple_registered = (register_simple_variants(), 0);
} // namespace
// === End block factory registration ===

simple::simple(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("simple", name(), bbMode)
        ,simpleBase(name(), variant)
        ,tag0("consumer_tag0", "producer")
        ,tag1("consumer_tag1", "producer")
        ,u_producer(std::dynamic_pointer_cast<producerBase>(instanceFactory::createInstance(name(), "u_producer", "producer", "", "simple")))
        ,u_consumer(std::dynamic_pointer_cast<consumerBase>(instanceFactory::createInstance(name(), "u_consumer", "consumer", "", "simple")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    u_producer->tag0(tag0);
    u_consumer->tag0(tag0);
    u_producer->tag1(tag1);
    u_consumer->tag1(tag1);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(doneTest);
};

// End-of-test bridge: the model is self-driving via testController. Wait for all
// registered tests to complete, then vote end-of-test so simpleExternal::eotThread
// can sc_stop() the simulation.
void simple::doneTest(void)
{
    endOfTest eot;
    eot.registerVoter();
    testController::GetInstance().wait_all_tests_complete();
    eot.setEndOfTest(true);
}

