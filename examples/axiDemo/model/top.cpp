// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include <memory>
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=top
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "top.h"
#include "producer_base.h"
#include "consumer_base.h"
SC_HAS_PROCESS(top);

top::registerBlock top::registerBlock_; //register the block with the factory

top::top(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("top", name(), bbMode)
        ,topBase(name(), variant)
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
        ,uProducer(std::dynamic_pointer_cast<producerBase>( instanceFactory::createInstance(name(), "uProducer", "producer", "")))
        ,uConsumer(std::dynamic_pointer_cast<consumerBase>( instanceFactory::createInstance(name(), "uConsumer", "consumer", "")))
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

}
