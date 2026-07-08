//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
#include "testController.h"

// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "producer.h"
SC_HAS_PROCESS(producer);

// === Block factory registration (producer) ===
void register_producer_variants() {
    instanceFactory::registerBlock("producer_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<producer>(blockName, variant, bbMode)); }, "", "simple");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _producer_registered = (register_producer_variants(), 0);
} // namespace
// === End block factory registration ===

producer::producer(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("producer", name(), bbMode)
        ,producerBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(outTag0);
    SC_THREAD(outTag1);
};

#define LOOPCOUNT 256

// Drive a sequence of tags out on tag0, registering and completing test_tag0.
void producer::outTag0(void)
{
    std::string test_name = "test_tag0";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    for (int loop = 0; loop < LOOPCOUNT; loop++)
    {
        tag_st t;
        t.tagId = loop % NUM_TAGS;
        tag0->push(t);
    }
    log_.logPrint(std::format("Test {} complete", test_name), LOG_ALWAYS);
    controller.test_complete(test_name);
}

// Drive a sequence of tags out on tag1, registering and completing test_tag1.
void producer::outTag1(void)
{
    std::string test_name = "test_tag1";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    for (int loop = 0; loop < LOOPCOUNT; loop++)
    {
        tag_st t;
        t.tagId = loop % NUM_TAGS;
        tag1->push(t);
    }
    log_.logPrint(std::format("Test {} complete", test_name), LOG_ALWAYS);
    controller.test_complete(test_name);
}

