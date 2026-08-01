//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=consumer --mode=module
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
export module simple_consumer.block;
import simple_consumer.base;
import simple;
using namespace simple_ns;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
export SC_MODULE(consumer), public blockBase, public consumerBase
{
private:

public:

    consumer(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~consumer() override = default;

    // GENERATED_CODE_END
    // block implementation members

    void inTag0(void);
    void inTag1(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(consumer);

// === Block factory registration (consumer) ===
void register_consumer_variants() {
    instanceFactory::registerBlock("consumer_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<consumer>(blockName, variant, bbMode)); }, "", "simple");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _consumer_registered = (register_consumer_variants(), 0);
} // namespace
// === End block factory registration ===

consumer::consumer(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("consumer", name(), bbMode)
        ,consumerBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(inTag0);
    SC_THREAD(inTag1);
};

#define LOOPCOUNT 256

// Receive and verify the tag sequence on tag0; completes test_tag0.
void consumer::inTag0(void)
{
    std::string test_name = "test_tag0";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    for (int loop = 0; loop < LOOPCOUNT; loop++)
    {
        tag_st t;
        tag0->pushReceive(t);
        tag0->ack();
        if (t.tagId != (tag)(loop % NUM_TAGS))
        {
            Q_ASSERT(false, "tag0 data mismatch");
        }
    }
    controller.test_complete(test_name);
}

// Receive and verify the tag sequence on tag1; completes test_tag1.
void consumer::inTag1(void)
{
    std::string test_name = "test_tag1";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    for (int loop = 0; loop < LOOPCOUNT; loop++)
    {
        tag_st t;
        tag1->pushReceive(t);
        tag1->ack();
        if (t.tagId != (tag)(loop % NUM_TAGS))
        {
            Q_ASSERT(false, "tag1 data mismatch");
        }
    }
    controller.test_complete(test_name);
}

