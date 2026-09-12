//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=consumer --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "pop_ack_channel.h"
#include "push_ack_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"
// GENERATED_CODE_END
#include "testController.h"
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module helloWorld_consumer.block;
import helloWorld_consumer.base;
import helloWorld_tb;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace helloWorld_tb_ns;
export SC_MODULE(consumer), public blockBase, public consumerBase
{
private:

public:

    consumer(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~consumer() override = default;

    // GENERATED_CODE_END
    // block implementation members

    std::shared_ptr<tracker<simpleString>> myTracker;
    void consumerInRdyVld(void);
    void consumerInReqAck(void);
    void consumerInPushAck(void);
    void consumerInPopAck(void);
    void consumerInRdyVldArb(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(consumer);

// === Block factory registration (consumer) ===
void register_consumer_variants() {
    instanceFactory::registerBlock("consumer_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<consumer>(blockName, variant, bbMode)); }, "", "helloWorld");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _consumer_registered = (register_consumer_variants(), 0);
} // namespace
// === End block factory registration ===

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
    SC_THREAD(consumerInRdyVldArb);
};

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
// Single consumer thread arbitrating between two rdy_vld producers with the
// documented pattern: bind both ports to one shared sc_event, scan isActive()
// under a wait loop, and service whichever port(s) woke the thread. Asserts
// each port's stream arrives in order (no lost wakeup, no misrouting) even
// though the two producers' first sends race in the same delta.
// ARB_TEST_COUNT must match the value used in producer.cppm.
#define ARB_TEST_COUNT 20
void consumer::consumerInRdyVldArb(void)
{
    std::string test_name = "test_rdy_vld_arb";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);

    sc_event arbEvent;
    test_rdy_vld_arb0->setExternalEvent(&arbEvent);
    test_rdy_vld_arb1->setExternalEvent(&arbEvent);

    int received0 = 0;
    int received1 = 0;
    data_st data;
    while (received0 < ARB_TEST_COUNT || received1 < ARB_TEST_COUNT) {
        while (test_rdy_vld_arb0->isNotActive() && test_rdy_vld_arb1->isNotActive()) {
            wait(arbEvent);
        }
        if (test_rdy_vld_arb0->isActive()) {
            test_rdy_vld_arb0->read(data);
            Q_ASSERT(data.b == (uint64_t)(1000 + received0), "arb0 data out of order or misrouted");
            received0++;
        }
        if (test_rdy_vld_arb1->isActive()) {
            test_rdy_vld_arb1->read(data);
            Q_ASSERT(data.b == (uint64_t)(2000 + received1), "arb1 data out of order or misrouted");
            received1++;
        }
    }
    log_.logPrint(std::format("test_rdy_vld_arb: received {} on arb0, {} on arb1", received0, received1), LOG_ALWAYS);
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

