// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "subBlockContainer.h"
#include "testController.h"


// GENERATED_CODE_PARAM --block=testBlock
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "testBlock.h"
SC_HAS_PROCESS(testBlock);

testBlock::registerBlock testBlock::registerBlock_; //register the block with the factory

testBlock::testBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("testBlock", name(), bbMode)
        ,testBlockBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END

    SC_THREAD(producerLoop1);
    SC_THREAD(producerLoop2);
    SC_THREAD(consumerLoop1);
    SC_THREAD(consumerLoop2);
}
void testBlock::producerLoop1()
{
    producer(loop1src);
}
void testBlock::producerLoop2()
{
    producer(loop2src);
}
void testBlock::consumerLoop1()
{
    consumer(loop1dst);
}
void testBlock::consumerLoop2()
{
    consumer(loop2dst);
}

void testBlock::producer(rdy_vld_out< test_st > &dataOut)
{
    testController &controller = testController::GetInstance();
    controller.register_test_name("test1");
    controller.wait_test("test1");

    test_st data;
    data.a = 0;
    wait(SC_ZERO_TIME);
    for(int i=0; i<10; i++) {
        data.a = i;
        std::cout << "write test " << data.a << endl;
        dataOut->write(data);
    }
    controller.test_complete("test1");
};

void testBlock::consumer(rdy_vld_in< test_st > &dataIn)
{
    testController &controller = testController::GetInstance();
    controller.register_test_name("test1");
    controller.wait_test("test1");

    test_st data;
    data.a=0;
    while (data.a < 9)
    {
        dataIn->read(data);
        std::cout << "read test " << data.a << endl;
    }
    controller.test_complete("test1");

}

