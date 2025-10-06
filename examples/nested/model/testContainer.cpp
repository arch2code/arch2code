// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE


// GENERATED_CODE_PARAM --block=testContainer
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "testContainer.h"
#include "testBlock_base.h"
#include "subBlockContainer_base.h"
#include "firstBlock_base.h"
#include "secondBlock_base.h"
#include "lastBlock_base.h"
#include "producer_base.h"
#include "consumer_base.h"
SC_HAS_PROCESS(testContainer);

testContainer::registerBlock testContainer::registerBlock_; //register the block with the factory

testContainer::testContainer(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("testContainer", name(), bbMode)
        ,testContainerBase(name(), variant)
        ,loop1a("testBlock_loop1a", "testBlock")
        ,loop1b("testBlock_loop1b", "testBlock")
        ,loop2a("subBlockContainer_loop2a", "testBlock")
        ,loop2b("testBlock_loop2b", "subBlockContainer")
        ,loop3a("subBlockContainer_loop3a", "testBlock")
        ,loop3b("subBlockContainer_loop3b", "subBlockContainer")
        ,loop3c("testBlock_loop3c", "subBlockContainer")
        ,primary("secondBlock_primary", "firstBlock")
        ,beta("lastBlock_beta", "secondBlock")
        ,response("firstBlock_response", "lastBlock")
        ,src_trans_dest_trans_rv_tracker("consumer_src_trans_dest_trans_rv_tracker", "producer", "api_list_tracker", 2048, "tracker:cmdid")
        ,src_clock_dest_trans_rv_tracker("consumer_src_clock_dest_trans_rv_tracker", "producer", "api_list_tracker", 2048, "tracker:cmdid")
        ,src_trans_dest_clock_rv_tracker("consumer_src_trans_dest_clock_rv_tracker", "producer", "api_list_tracker", 2048, "tracker:cmdid")
        ,src_trans_dest_trans_rv_size("consumer_src_trans_dest_trans_rv_size", "producer", "api_list_size", 1024, "")
        ,src_clock_dest_trans_rv_size("consumer_src_clock_dest_trans_rv_size", "producer", "api_list_size", 2048, "")
        ,src_trans_dest_clock_rv_size("consumer_src_trans_dest_clock_rv_size", "producer", "api_list_size", 2048, "")
        ,uTestBlock0(std::dynamic_pointer_cast<testBlockBase>( instanceFactory::createInstance(name(), "uTestBlock0", "testBlock", "")))
        ,uTestBlock1(std::dynamic_pointer_cast<testBlockBase>( instanceFactory::createInstance(name(), "uTestBlock1", "testBlock", "")))
        ,uSubBlockContainer0(std::dynamic_pointer_cast<subBlockContainerBase>( instanceFactory::createInstance(name(), "uSubBlockContainer0", "subBlockContainer", "")))
        ,uSubBlockContainer1(std::dynamic_pointer_cast<subBlockContainerBase>( instanceFactory::createInstance(name(), "uSubBlockContainer1", "subBlockContainer", "")))
        ,uSubBlockContainer2(std::dynamic_pointer_cast<subBlockContainerBase>( instanceFactory::createInstance(name(), "uSubBlockContainer2", "subBlockContainer", "")))
        ,uFirst(std::dynamic_pointer_cast<firstBlockBase>( instanceFactory::createInstance(name(), "uFirst", "firstBlock", "")))
        ,uSecond(std::dynamic_pointer_cast<secondBlockBase>( instanceFactory::createInstance(name(), "uSecond", "secondBlock", "")))
        ,uLast(std::dynamic_pointer_cast<lastBlockBase>( instanceFactory::createInstance(name(), "uLast", "lastBlock", "")))
        ,uProducer(std::dynamic_pointer_cast<producerBase>( instanceFactory::createInstance(name(), "uProducer", "producer", "")))
        ,uConsumer(std::dynamic_pointer_cast<consumerBase>( instanceFactory::createInstance(name(), "uConsumer", "consumer", "")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uTestBlock0->loop1src(loop1a);
    uTestBlock1->loop1dst(loop1a);
    uTestBlock1->loop1src(loop1b);
    uTestBlock0->loop1dst(loop1b);
    uTestBlock0->loop2src(loop2a);
    uSubBlockContainer0->in(loop2a);
    uSubBlockContainer0->out(loop2b);
    uTestBlock0->loop2dst(loop2b);
    uTestBlock1->loop2src(loop3a);
    uSubBlockContainer1->in(loop3a);
    uSubBlockContainer1->out(loop3b);
    uSubBlockContainer2->in(loop3b);
    uSubBlockContainer2->out(loop3c);
    uTestBlock1->loop2dst(loop3c);
    uFirst->primary(primary);
    uSecond->primary(primary);
    uSecond->beta(beta);
    uLast->beta(beta);
    uLast->response(response);
    uFirst->response(response);
    uProducer->src_trans_dest_trans_rv_tracker(src_trans_dest_trans_rv_tracker);
    uConsumer->src_trans_dest_trans_rv_tracker(src_trans_dest_trans_rv_tracker);
    uProducer->src_clock_dest_trans_rv_tracker(src_clock_dest_trans_rv_tracker);
    uConsumer->src_clock_dest_trans_rv_tracker(src_clock_dest_trans_rv_tracker);
    uProducer->src_trans_dest_clock_rv_tracker(src_trans_dest_clock_rv_tracker);
    uConsumer->src_trans_dest_clock_rv_tracker(src_trans_dest_clock_rv_tracker);
    uProducer->src_trans_dest_trans_rv_size(src_trans_dest_trans_rv_size);
    uConsumer->src_trans_dest_trans_rv_size(src_trans_dest_trans_rv_size);
    uProducer->src_clock_dest_trans_rv_size(src_clock_dest_trans_rv_size);
    uConsumer->src_clock_dest_trans_rv_size(src_clock_dest_trans_rv_size);
    uProducer->src_trans_dest_clock_rv_size(src_trans_dest_clock_rv_size);
    uConsumer->src_trans_dest_clock_rv_size(src_trans_dest_clock_rv_size);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END

}
