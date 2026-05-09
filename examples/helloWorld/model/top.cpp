// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <memory>
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=top
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "top.h"
#include "producer_base.h"
#include "consumer_base.h"
SC_HAS_PROCESS(top);

// === Block factory registration (top) ===
void force_link_top() {}

void register_top_variants() {
    instanceFactory::registerBlock("top_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<top>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _top_registered = (register_top_variants(), 0);
} // namespace
// === End block factory registration ===

top::top(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("top", name(), bbMode)
        ,topBase(name(), variant)
        ,test_rdy_vld("consumer_test_rdy_vld", "producer")
        ,test_req_ack("consumer_test_req_ack", "producer")
        ,test_push_ack("consumer_test_push_ack", "producer")
        ,test_pop_ack("consumer_test_pop_ack", "producer")
        ,uProducer(std::dynamic_pointer_cast<producerBase>((force_link_producer(), instanceFactory::createInstance(name(), "uProducer", "producer", ""))))
        ,uConsumer(std::dynamic_pointer_cast<consumerBase>((force_link_consumer(), instanceFactory::createInstance(name(), "uConsumer", "consumer", ""))))
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
    //auto baseInstance = instanceFactory::createInstance("uProducer");
    //uProducer2 = (producer *) baseInstance.get();
}
