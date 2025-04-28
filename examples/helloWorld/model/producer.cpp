// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "testController.h"
#include "tagTrackers.h"

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
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(fmt::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(producerOutRdyVld);
    SC_THREAD(producerOutPopAck);
    SC_THREAD(producerOutReqAck);
    SC_THREAD(producerOutPushAck);
}

void producer::producerOutRdyVld(void)
{
    std::string test_name = "test_rdy_vld";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    data_st data;

    data.b = 0;
    wait(SC_ZERO_TIME);
    log_.logPrint("RV1");
    test_rdy_vld->write(data);
    log_.logPrint("RV2");
    wait(SC_ZERO_TIME);
    wait(SC_ZERO_TIME);
    wait(SC_ZERO_TIME);
    log_.logPrint("RV3");
    data.b = 1;
    test_rdy_vld->write(data);
    log_.logPrint("RV4");
    data.b = 0;
    test_rdy_vld->write(data);
    log_.logPrint("RV5");
    controller.test_complete(test_name);   

}
void producer::producerOutReqAck(void)
{
    std::string test_name = "test_req_ack";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    data_st reqData;
    data_st ackData;

    reqData.b = 0;
    wait(SC_ZERO_TIME);
    log_.logPrint("RQA1");
    test_req_ack->req(reqData, ackData);
    log_.logPrint("RQA2");
    wait(SC_ZERO_TIME);
    wait(SC_ZERO_TIME);
    wait(SC_ZERO_TIME);
    log_.logPrint("RQA3");
    reqData.b = 1;
    test_req_ack->req(reqData, ackData);
    log_.logPrint("RQA4");
    reqData.b = 0;
    test_req_ack->req(reqData, ackData);
    log_.logPrint("RQA5");
    controller.test_complete(test_name);   

}
void producer::producerOutPushAck(void)
{
    std::string test_name = "test_push_ack";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    data_st data;

    data.b = 0;
    wait(SC_ZERO_TIME);
    log_.logPrint("VA1");
    test_push_ack->push(data);
    log_.logPrint("VA2");
    wait(SC_ZERO_TIME);
    wait(SC_ZERO_TIME);
    wait(SC_ZERO_TIME);
    log_.logPrint("VA3");
    data.b = 1;
    test_push_ack->push(data);
    log_.logPrint("VA4");
    data.b = 0;
    test_push_ack->push(data);
    log_.logPrint("VA5");
    controller.test_complete(test_name);   
}

void producer::producerOutPopAck(void)
{
    std::string test_name = "test_pop_ack";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    data_st ackData;

    wait(SC_ZERO_TIME);
    log_.logPrint("RDA1");
    test_pop_ack->pop(ackData);
    log_.logPrint("RDA2");
    wait(SC_ZERO_TIME);
    wait(SC_ZERO_TIME);
    wait(SC_ZERO_TIME);
    log_.logPrint("RDA3");
    test_pop_ack->pop(ackData);
    log_.logPrint("RDA4");
    test_pop_ack->pop(ackData);
    log_.logPrint("RDA5");
    controller.test_complete(test_name);   

}
