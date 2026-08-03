//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=testContainer --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "rdy_vld_channel.h"
// GENERATED_CODE_END
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module nested_testContainer.block;
import nested_testContainer.base;
import nested;
import nested_testBlock.base;
import nested_subBlockContainer.base;
import nested_firstBlock.base;
import nested_secondBlock.base;
import nested_lastBlock.base;
import nested_producer.base;
import nested_consumer.base;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace nested_ns;
export SC_MODULE(testContainer), public blockBase, public testContainerBase
{
private:

public:
    // channels
    // Test interface
    rdy_vld_channel< test_st > loop1a;
    // Test interface
    rdy_vld_channel< test_st > loop1b;
    // Test interface
    rdy_vld_channel< test_st > loop2a;
    // Test interface
    rdy_vld_channel< test_st > loop2b;
    // Test interface
    rdy_vld_channel< test_st > loop3a;
    // Test interface
    rdy_vld_channel< test_st > loop3b;
    // Test interface
    rdy_vld_channel< test_st > loop3c;
    // Test interface alpha
    rdy_vld_channel< test_st > primary;
    // Test interface beta
    rdy_vld_channel< test_st > beta;
    // Test interface gamma
    rdy_vld_channel< test_st > response;
    // Data path test interface
    rdy_vld_channel< testDataSt > src_trans_dest_trans_rv_tracker;
    // Data path test interface
    rdy_vld_channel< testDataSt > src_clock_dest_trans_rv_tracker;
    // Data path test interface
    rdy_vld_channel< testDataSt > src_trans_dest_clock_rv_tracker;
    // Data path test interface
    rdy_vld_channel< testDataSt > src_trans_dest_trans_rv_size;
    // Data path test interface
    rdy_vld_channel< testDataSt > src_clock_dest_trans_rv_size;
    // Data path test interface
    rdy_vld_channel< testDataSt > src_trans_dest_clock_rv_size;

    //instances contained in block
    std::shared_ptr<testBlockBase> uTestBlock0;
    std::shared_ptr<testBlockBase> uTestBlock1;
    std::shared_ptr<subBlockContainerBase> uSubBlockContainer0;
    std::shared_ptr<subBlockContainerBase> uSubBlockContainer1;
    std::shared_ptr<subBlockContainerBase> uSubBlockContainer2;
    std::shared_ptr<firstBlockBase> uFirst;
    std::shared_ptr<secondBlockBase> uSecond;
    std::shared_ptr<lastBlockBase> uLast;
    std::shared_ptr<producerBase> uProducer;
    std::shared_ptr<consumerBase> uConsumer;

    testContainer(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~testContainer() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(testContainer);

// === Block factory registration (testContainer) ===
void register_testContainer_variants() {
    instanceFactory::registerBlock("testContainer_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<testContainer>(blockName, variant, bbMode)); }, "", "nested");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _testContainer_registered = (register_testContainer_variants(), 0);
} // namespace
// === End block factory registration ===

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
        ,uTestBlock0(std::dynamic_pointer_cast<testBlockBase>(instanceFactory::createInstance(name(), "uTestBlock0", "testBlock", "", "nested")))
        ,uTestBlock1(std::dynamic_pointer_cast<testBlockBase>(instanceFactory::createInstance(name(), "uTestBlock1", "testBlock", "", "nested")))
        ,uSubBlockContainer0(std::dynamic_pointer_cast<subBlockContainerBase>(instanceFactory::createInstance(name(), "uSubBlockContainer0", "subBlockContainer", "", "nested")))
        ,uSubBlockContainer1(std::dynamic_pointer_cast<subBlockContainerBase>(instanceFactory::createInstance(name(), "uSubBlockContainer1", "subBlockContainer", "", "nested")))
        ,uSubBlockContainer2(std::dynamic_pointer_cast<subBlockContainerBase>(instanceFactory::createInstance(name(), "uSubBlockContainer2", "subBlockContainer", "", "nested")))
        ,uFirst(std::dynamic_pointer_cast<firstBlockBase>(instanceFactory::createInstance(name(), "uFirst", "firstBlock", "", "nested")))
        ,uSecond(std::dynamic_pointer_cast<secondBlockBase>(instanceFactory::createInstance(name(), "uSecond", "secondBlock", "", "nested")))
        ,uLast(std::dynamic_pointer_cast<lastBlockBase>(instanceFactory::createInstance(name(), "uLast", "lastBlock", "", "nested")))
        ,uProducer(std::dynamic_pointer_cast<producerBase>(instanceFactory::createInstance(name(), "uProducer", "producer", "", "nested")))
        ,uConsumer(std::dynamic_pointer_cast<consumerBase>(instanceFactory::createInstance(name(), "uConsumer", "consumer", "", "nested")))
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
};

