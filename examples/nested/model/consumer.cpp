// copyright contributors to arch2code project 2022
#include "consumer.h"
#include "testController.h"


// GENERATED_CODE_PARAM --block=consumer
// GENERATED_CODE_BEGIN --template=constructor --section=init 
#include "consumer.h"
SC_HAS_PROCESS(consumer);

consumer::registerBlock consumer::registerBlock_; //register the block with the factory

consumer::consumer(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("consumer", name(), bbMode)
        ,consumerBase(name(), variant)
// GENERATED_CODE_END
        ,testSizes({128, 256, 512, 1024})
        ,cmdTracker(std::static_pointer_cast< tracker < simpleString > >( trackerCollection::GetInstance().getTracker("cmdid") ))
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(fmt::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(consumerInRdyVldSizeTransactional1);
    SC_THREAD(consumerInRdyVldSizeTransactional2);
    SC_THREAD(consumerInRdyVldSizeNonTransactional);
    SC_THREAD(consumerInRdyVldTrackerTransactional1);
    SC_THREAD(consumerInRdyVldTrackerTransactional2);
    SC_THREAD(consumerInRdyVldTrackerNonTransactional);
}



// test case for rdyVld where size of transfer is provided via api
void consumer::consumerInRdyVldSizeTransactional1(void)
{
    std::string test_name = "src_trans_dest_trans_rv_size";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    consumerInRdyVldSizeTransactional(src_trans_dest_trans_rv_size, test_name);
    controller.test_complete(test_name);
}
void consumer::consumerInRdyVldSizeTransactional2(void)
{
    std::string test_name = "src_clock_dest_trans_rv_size";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    consumerInRdyVldSizeTransactional(src_clock_dest_trans_rv_size, test_name);
    controller.test_complete(test_name);
}

void consumer::consumerInRdyVldSizeTransactional(rdy_vld_in< testDataSt > &inPort, std::string name_)
{
    testDataSt test;
    // as the producer may not be transactional, we need to provide the transactional contexts to allow non-transactional -> transactional conversion
    for( auto testSize : testSizes )
    {
        inPort->push_context(testSize);
    }
    int testCase = 0;
    for( auto testSize : testSizes )
    {
        inPort->read(test);
        uint8_t *data = inPort->getReadPtr();
        for(uint32_t i=0; i<testSize; i++)
        {
            // check if every byte is the same as the cmdid in the hdr
            if(data[i] != testCase)
            {
                log_.logPrint(fmt::format("ERROR: {} {}", name_, test.prt()) );
                Q_ASSERT(false, "ERROR: consumerInRdyVldTransactional");
            }
        } 
        testCase++;
    }
}

void consumer::consumerInRdyVldSizeNonTransactional(void)
{
    src_trans_dest_clock_rv_size->setCycleTransaction();
    testDataSt test;
    std::string test_name = "src_trans_dest_clock_rv_size";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);

    int testCase = 0;
    for(auto testSize : testSizes)
    {
        int num_cycles = testSize / sizeof(test);

        for(int cycle=0;  cycle<num_cycles ; cycle++)
        {
            src_trans_dest_clock_rv_size->readClocked(test);

            // check the results
            for(int i=0; i<(int)sizeof(test); i++)
            {
                // check if every byte is the same as the cmdid in the hdr
                if(*(((uint8_t *)&test.data) + i) != testCase)
                {
                    log_.logPrint(fmt::format("ERROR: {} {}", test_name, test.prt()) );
                    Q_ASSERT(false, "ERROR: consumerInRdyVldSizeNonTransactional");
                }
            } 
        }
        testCase++;
    }
    controller.test_complete(test_name);   
}


// test case for rdyVld where size of transfer is provided by tracker via api
void consumer::consumerInRdyVldTrackerTransactional1(void)
{
    std::string test_name = "src_trans_dest_trans_rv_tracker";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    consumerInRdyVldTrackerTransactional(src_trans_dest_trans_rv_tracker, test_name);
    controller.test_complete(test_name);
}
void consumer::consumerInRdyVldTrackerTransactional2(void)
{
    std::string test_name = "src_clock_dest_trans_rv_tracker";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    consumerInRdyVldTrackerTransactional(src_clock_dest_trans_rv_tracker, test_name);
    controller.test_complete(test_name);
}

void consumer::consumerInRdyVldTrackerTransactional(rdy_vld_in< testDataSt > &inPort, std::string name_)
{
    testDataSt test;
    // as the producer may not be transactional, we need to provide the transactional contexts to allow non-transactional -> transactional conversion
    int testCase = 0;
    for( auto testSize : testSizes )
    {
        inPort->push_context(testCase);
        testCase++;
    }
    testCase = 0;
    for( auto testSize : testSizes )
    {
        inPort->read(test);
        uint8_t *data = cmdTracker->getBackdoorPtr(testCase); // get a pointer to the backdoor data buffer
        for(uint32_t i=0; i<testSize; i++)
        {
            // check if every byte is the same as the cmdid in the hdr
            if(data[i] != testCase)
            {
                log_.logPrint(fmt::format("ERROR: {} {}", name_, test.prt()) );
                Q_ASSERT(false, "ERROR: consumerInRdyVldTrackerTransactional");
            }
        } 
        testCase++;
    }

    

}

void consumer::consumerInRdyVldTrackerNonTransactional(void)
{
    src_trans_dest_clock_rv_tracker->setCycleTransaction();
    testDataSt test;
    std::string test_name = "src_trans_dest_clock_rv_tracker";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);

    int testCase = 0;
    for(auto testSize : testSizes)
    {
        int num_cycles = testSize / sizeof(test);

        for(int cycle=0;  cycle<num_cycles ; cycle++)
        {
            src_trans_dest_clock_rv_tracker->readClocked(test);

            // check the results
            for(int i=0; i<(int)sizeof(test); i++)
            {
                // check if every byte is the same as the cmdid in the hdr
                if(*(((uint8_t *)&test.data) + i) != testCase)
                {
                    log_.logPrint(fmt::format("ERROR: {} {}", test_name, test.prt()) );
                    Q_ASSERT(false, "ERROR: consumerInRdyVldTrackerNonTransactional");
                }
            } 
        }
        testCase++;
    }
    controller.test_complete(test_name);   
}
