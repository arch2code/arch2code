//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "endOfTest.h"
#include "testController.h"

// GENERATED_CODE_PARAM --block=axiDemo
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "axiDemo.h"
#include "producerBase.h"
#include "consumerBase.h"
SC_HAS_PROCESS(axiDemo);

// === Block factory registration (axiDemo) ===
void force_link_axiDemo() {}

void register_axiDemo_variants() {
    instanceFactory::registerBlock("axiDemo_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<axiDemo>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _axiDemo_registered = (register_axiDemo_variants(), 0);
} // namespace
// === End block factory registration ===

axiDemo::axiDemo(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("axiDemo", name(), bbMode)
        ,axiDemoBase(name(), variant)
        ,axiRd0("consumer_axiRd0", "producer", "api_list_size", 256, "")
        ,axiRd1("consumer_axiRd1", "producer", "api_list_size", 256, "")
        ,axiRd2("consumer_axiRd2", "producer", "api_list_size", 256, "")
        ,axiRd3("consumer_axiRd3", "producer", "api_list_size", 256, "")
        ,axiWr0("consumer_axiWr0", "producer", "api_list_size", 256, "")
        ,axiWr1("consumer_axiWr1", "producer", "api_list_size", 256, "")
        ,axiWr2("consumer_axiWr2", "producer", "api_list_size", 256, "")
        ,axiWr3("consumer_axiWr3", "producer", "api_list_size", 256, "")
        ,axiStr0("consumer_axiStr0", "producer", "api_list_size", 256, "")
        ,axiStr1("consumer_axiStr1", "producer", "api_list_size", 256, "")
        ,uProducer(std::dynamic_pointer_cast<producerBase>((force_link_producer(), instanceFactory::createInstance(name(), "uProducer", "producer", ""))))
        ,uConsumer(std::dynamic_pointer_cast<consumerBase>((force_link_consumer(), instanceFactory::createInstance(name(), "uConsumer", "consumer", ""))))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uProducer->axiRd0(axiRd0);
    uConsumer->axiRd0(axiRd0);
    uProducer->axiRd1(axiRd1);
    uConsumer->axiRd1(axiRd1);
    uProducer->axiRd2(axiRd2);
    uConsumer->axiRd2(axiRd2);
    uProducer->axiRd3(axiRd3);
    uConsumer->axiRd3(axiRd3);
    uProducer->axiWr0(axiWr0);
    uConsumer->axiWr0(axiWr0);
    uProducer->axiWr1(axiWr1);
    uConsumer->axiWr1(axiWr1);
    uProducer->axiWr2(axiWr2);
    uConsumer->axiWr2(axiWr2);
    uProducer->axiWr3(axiWr3);
    uConsumer->axiWr3(axiWr3);
    uProducer->axiStr0(axiStr0);
    uConsumer->axiStr0(axiStr0);
    uProducer->axiStr1(axiStr1);
    uConsumer->axiStr1(axiStr1);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(doneTest);
};

// End-of-test bridge: the model is self-driving via testController. Wait for all
// registered tests to complete, then vote end-of-test so axiDemoExternal::eotThread
// can sc_stop() the simulation.
void axiDemo::doneTest(void)
{
    endOfTest eot;
    eot.registerVoter();
    testController::GetInstance().wait_all_tests_complete();
    eot.setEndOfTest(true);
}

