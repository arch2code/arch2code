// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
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
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(consumerInRdyVld);
    SC_THREAD(consumerInReqAck);
    SC_THREAD(consumerInPushAck);
    SC_THREAD(consumerInPopAck);

}
void consumer::consumerInRdyVld(void)
{
    std::string test_name = "test_rdy_vld";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    data_st data;
    log_.logPrint("RV0");
    wait(SC_ZERO_TIME);
    wait(SC_ZERO_TIME);
    log_.logPrint("RV1");
    test_rdy_vld->read(data);
    log_.logPrint("RV2");
    test_rdy_vld->read(data);
    log_.logPrint("RV3");
    wait(SC_ZERO_TIME);
    wait(SC_ZERO_TIME);
    test_rdy_vld->read(data);
    log_.logPrint("RV4");
    controller.test_complete(test_name);

}
void consumer::consumerInReqAck(void)
{
    std::string test_name = "test_req_ack";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    data_st reqData;
    data_st ackData;
    log_.logPrint("RQA0");
    wait(SC_ZERO_TIME);
    wait(SC_ZERO_TIME);
    log_.logPrint("RQA1");
    test_req_ack->reqReceive(reqData);
    ackData = reqData;
    test_req_ack->ack(ackData);
    log_.logPrint("RQA2");
    test_req_ack->reqReceive(reqData);
    ackData = reqData;
    test_req_ack->ack(ackData);
    log_.logPrint("RQA3");
    wait(SC_ZERO_TIME);
    wait(SC_ZERO_TIME);
    test_req_ack->reqReceive(reqData);
    ackData = reqData;
    test_req_ack->ack(ackData);
    log_.logPrint("RQA4");
    controller.test_complete(test_name);

}
void consumer::consumerInPushAck(void)
{
    std::string test_name = "test_push_ack";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    data_st data;
    log_.logPrint("VA0");
    wait(SC_ZERO_TIME);
    wait(SC_ZERO_TIME);
    log_.logPrint("VA1");
    test_push_ack->pushReceive(data);
    log_.logPrint("VA2");
    test_push_ack->ack();
    log_.logPrint("VA3");
    test_push_ack->pushReceive(data);
    log_.logPrint("VA4");
    test_push_ack->ack();
    log_.logPrint("VA5");
    wait(SC_ZERO_TIME);
    wait(SC_ZERO_TIME);
    test_push_ack->pushReceive(data);
    log_.logPrint("VA6");
    test_push_ack->ack();
    log_.logPrint("VA7");
    controller.test_complete(test_name);

}
void consumer::consumerInPopAck(void)
{
    std::string test_name = "test_pop_ack";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    data_st ackData;
    log_.logPrint("RDA0");
    wait(SC_ZERO_TIME);
    wait(SC_ZERO_TIME);
    log_.logPrint("RDA1");
    test_pop_ack->popReceive();
    ackData.b = 0;
    test_pop_ack->ack(ackData);
    log_.logPrint("RDA2");
    test_pop_ack->popReceive();
    ackData.b = 1;
    test_pop_ack->ack(ackData);
    log_.logPrint("RDA3");
    wait(SC_ZERO_TIME);
    wait(SC_ZERO_TIME);
    test_pop_ack->popReceive();
    ackData.b = 0;
    test_pop_ack->ack(ackData);
    log_.logPrint("RDA4");
    controller.test_complete(test_name);

}

