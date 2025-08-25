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
        ,loop1src_uTestBlock0_uTestBlock1("testBlock_loop1src_uTestBlock0_uTestBlock1", "testBlock")
        ,loop1src_uTestBlock1_uTestBlock0("testBlock_loop1src_uTestBlock1_uTestBlock0", "testBlock")
        ,loop2src_uTestBlock0_uSubBlockContainer0("subBlockContainer_loop2src_uTestBlock0_uSubBlockContainer0", "testBlock")
        ,out_uSubBlockContainer0_uTestBlock0("testBlock_out_uSubBlockContainer0_uTestBlock0", "subBlockContainer")
        ,loop2src_uTestBlock1_uSubBlockContainer1("subBlockContainer_loop2src_uTestBlock1_uSubBlockContainer1", "testBlock")
        ,out_uSubBlockContainer2_uTestBlock1("testBlock_out_uSubBlockContainer2_uTestBlock1", "subBlockContainer")
        ,out_uSubBlockContainer1_uSubBlockContainer2("subBlockContainer_out_uSubBlockContainer1_uSubBlockContainer2", "subBlockContainer")
        ,primary("secondBlock_primary", "firstBlock")
        ,response("firstBlock_response", "lastBlock")
        ,beta("lastBlock_beta", "secondBlock")
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
    uTestBlock0->loop1src(loop1src_uTestBlock0_uTestBlock1);
    uTestBlock1->loop1dst(loop1src_uTestBlock0_uTestBlock1);
    uTestBlock1->loop1src(loop1src_uTestBlock1_uTestBlock0);
    uTestBlock0->loop1dst(loop1src_uTestBlock1_uTestBlock0);
    uTestBlock0->loop2src(loop2src_uTestBlock0_uSubBlockContainer0);
    uSubBlockContainer0->in(loop2src_uTestBlock0_uSubBlockContainer0);
    uSubBlockContainer0->out(out_uSubBlockContainer0_uTestBlock0);
    uTestBlock0->loop2dst(out_uSubBlockContainer0_uTestBlock0);
    uTestBlock1->loop2src(loop2src_uTestBlock1_uSubBlockContainer1);
    uSubBlockContainer1->in(loop2src_uTestBlock1_uSubBlockContainer1);
    uSubBlockContainer2->out(out_uSubBlockContainer2_uTestBlock1);
    uTestBlock1->loop2dst(out_uSubBlockContainer2_uTestBlock1);
    uSubBlockContainer1->out(out_uSubBlockContainer1_uSubBlockContainer2);
    uSubBlockContainer2->in(out_uSubBlockContainer1_uSubBlockContainer2);
    uFirst->primary(primary);
    uSecond->primary(primary);
    uLast->response(response);
    uFirst->response(response);
    uSecond->beta(beta);
    uLast->beta(beta);
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
