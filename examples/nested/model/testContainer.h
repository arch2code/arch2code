#ifndef TESTCONTAINER_H
#define TESTCONTAINER_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"


// GENERATED_CODE_PARAM --block=testContainer
// GENERATED_CODE_BEGIN --template=classDecl 
#include "logging.h"
#include "instanceFactory.h"
#include "testContainer_base.h"
#include "nestedTopIncludes.h"
//contained instances forward class declaration
class testBlockBase;
class subBlockContainerBase;
class firstBlockBase;
class secondBlockBase;
class lastBlockBase;
class producerBase;
class consumerBase;

SC_MODULE(testContainer), public blockBase, public testContainerBase
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("testContainer_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<testContainer>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:

    // channels
    //   test
    rdy_vld_channel< test_st > loop1src_uTestBlock0_uTestBlock1;
    //   test
    rdy_vld_channel< test_st > loop1src_uTestBlock1_uTestBlock0;
    //   test
    rdy_vld_channel< test_st > loop2src_uTestBlock0_uSubBlockContainer0;
    //   test
    rdy_vld_channel< test_st > out_uSubBlockContainer0_uTestBlock0;
    //   test
    rdy_vld_channel< test_st > loop2src_uTestBlock1_uSubBlockContainer1;
    //   test
    rdy_vld_channel< test_st > out_uSubBlockContainer2_uTestBlock1;
    //   test
    rdy_vld_channel< test_st > out_uSubBlockContainer1_uSubBlockContainer2;
    //   alpha
    rdy_vld_channel< test_st > primary;
    //   gamma
    rdy_vld_channel< test_st > response;
    //   beta
    rdy_vld_channel< test_st > beta;
    //   testrvTracker
    rdy_vld_channel< testDataSt > src_trans_dest_trans_rv_tracker;
    //   testrvTracker
    rdy_vld_channel< testDataSt > src_clock_dest_trans_rv_tracker;
    //   testrvTracker
    rdy_vld_channel< testDataSt > src_trans_dest_clock_rv_tracker;
    //   testrvSize
    rdy_vld_channel< testDataSt > src_trans_dest_trans_rv_size;
    //   testrvSize
    rdy_vld_channel< testDataSt > src_clock_dest_trans_rv_size;
    //   testrvSize
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

#endif //TESTCONTAINER_H

