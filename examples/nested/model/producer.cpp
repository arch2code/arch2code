// copyright contributors to arch2code project 2022
#include "testController.h"
#include "tracker.h"


// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=constructor --section=init 
#include "producer.h"
SC_HAS_PROCESS(producer);

producer::registerBlock producer::registerBlock_; //register the block with the factory

producer::producer(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("producer", name(), bbMode)
        ,producerBase(name(), variant)
// GENERATED_CODE_END
        ,testSizes({128, 256, 512, 1024})
        ,cmdTracker(std::static_pointer_cast< tracker < simpleString > >( trackerCollection::GetInstance().getTracker("cmdid") ))
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(fmt::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(producerOutRdyVldSizeTransactional1);
    SC_THREAD(producerOutRdyVldSizeTransactional2);
    SC_THREAD(producerOutRdyVldSizeNonTransactional);
    SC_THREAD(producerOutRdyVldTrackerTransactional1);
    SC_THREAD(producerOutRdyVldTrackerTransactional2);
    SC_THREAD(producerOutRdyVldTrackerNonTransactional);

    int i=0;
    // allocate cmdids in tracker
    for(auto testSize : testSizes)
    {
        // allocate space for buffer of size testSize
        buffers.push_back( std::make_shared<std::vector<uint8_t> >(testSize) );
        cmdTracker->alloc(i, std::make_shared<simpleString>(fmt::format("Command %i Length 0x{:x}", i, testSize)), getTrackerRefCountDelta());
        cmdTracker->setLen(i, testSize);
        cmdTracker->initBackdoorPtr(i, buffers[i]->data() );
        i++;
    }

}



// test case for rdyVld where size of transfer is provided via api 
void producer::producerOutRdyVldSizeTransactional1(void)
{
    std::string test_name = "src_trans_dest_trans_rv_size";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    producerOutRdyVldSizeTransactional(src_trans_dest_trans_rv_size, test_name);
    controller.test_complete(test_name);

}
void producer::producerOutRdyVldSizeTransactional2(void)
{
    std::string test_name = "src_trans_dest_clock_rv_size";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    producerOutRdyVldSizeTransactional(src_trans_dest_clock_rv_size, test_name);
    controller.test_complete(test_name);

}
void producer::producerOutRdyVldSizeTransactional(rdy_vld_out< testDataSt > &outPort, std::string name)
{
    wait(SC_ZERO_TIME); // wait for reader to initialize sizes
    // iterate over test sizes
    int testCase = 0;
    for(auto testSize : testSizes)
    {
        // iterate over test data           
        testDataSt test;

        uint8_t * data = outPort->getWritePtr(); // get a pointer to the backdoor data buffer
        memset(data, testCase, testSize);
    
        outPort->write(test, testSize); // passing in size to the write function to provide context in variable size case
        testCase++;
    }
}

// in non-transactional test case we do not provide any size information to the write function
void producer::producerOutRdyVldSizeNonTransactional(void)
{
    src_clock_dest_trans_rv_size->setCycleTransaction();
    std::string test_name = "src_clock_dest_trans_rv_size";

    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    wait(SC_ZERO_TIME); // wait for reader to initialize sizes
    int testCase = 0;
    for(auto testSize : testSizes)
    {
        testDataSt test;

        memset(&test.data, testCase, sizeof(test));
        int num_cycles = testSize / sizeof(test);

        for(int cycle=0; cycle<num_cycles; cycle++)
        {
            src_clock_dest_trans_rv_size->writeClocked(test);
        } 
        testCase++;      
    }
    controller.test_complete(test_name);

}

// test case for rdyVld where size of transfer is provided by tracker via api
void producer::producerOutRdyVldTrackerTransactional1(void)
{
    std::string test_name = "src_trans_dest_trans_rv_tracker";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    producerOutRdyVldTrackerTransactional(src_trans_dest_trans_rv_tracker, test_name);
    controller.test_complete(test_name);

}
void producer::producerOutRdyVldTrackerTransactional2(void)
{
    std::string test_name = "src_trans_dest_clock_rv_tracker";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    producerOutRdyVldTrackerTransactional(src_trans_dest_clock_rv_tracker, test_name);
    controller.test_complete(test_name);

}
void producer::producerOutRdyVldTrackerTransactional(rdy_vld_out< testDataSt > &outPort, std::string name)
{
    wait(SC_ZERO_TIME); // wait for reader to initialize sizes
    // iterate over test sizes
    int testCase = 0;
    for(auto testSize : testSizes)
    {
        // iterate over test data           
        testDataSt test;

        uint8_t * data = cmdTracker->getBackdoorPtr(testCase); // get a pointer to the backdoor data buffer
        memset(data, testCase, testSize);
    
        outPort->write(test, testCase); // passing in size to the write function to provide context in variable size case
        testCase++;
    }


}

// in non-transactional test case we do not provide any size information to the write function
void producer::producerOutRdyVldTrackerNonTransactional(void)
{
    src_clock_dest_trans_rv_tracker->setCycleTransaction();
    std::string test_name = "src_clock_dest_trans_rv_tracker";

    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    wait(SC_ZERO_TIME); // wait for reader to initialize sizes
    int testCase = 0;
    for(auto testSize : testSizes)
    {
        testDataSt test;

        memset(&test.data, testCase, sizeof(test));
        int num_cycles = testSize / sizeof(test);

        for(int cycle=0; cycle<num_cycles; cycle++)
        {
            src_clock_dest_trans_rv_tracker->writeClocked(test);
        } 
        testCase++;      
    }
    controller.test_complete(test_name);

}
