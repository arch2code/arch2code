//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "endOfTest.h"
#include "testController.h"

// GENERATED_CODE_PARAM --block=simple
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "simple.h"
#include "producerBase.h"
#include "consumerBase.h"
SC_HAS_PROCESS(simple);

// === Block factory registration (simple) ===
void force_link_simple() {}

void register_simple_variants() {
    instanceFactory::registerBlock("simple_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<simple>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _simple_registered = (register_simple_variants(), 0);
} // namespace
// === End block factory registration ===

simple::simple(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("simple", name(), bbMode)
        ,simpleBase(name(), variant)
        ,tag0("consumer_tag0", "producer")
        ,tag1("consumer_tag1", "producer")
        ,u_producer(std::dynamic_pointer_cast<producerBase>((force_link_producer(), instanceFactory::createInstance(name(), "u_producer", "producer", ""))))
        ,u_consumer(std::dynamic_pointer_cast<consumerBase>((force_link_consumer(), instanceFactory::createInstance(name(), "u_consumer", "consumer", ""))))
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

