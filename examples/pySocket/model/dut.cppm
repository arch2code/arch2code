//

// GENERATED_CODE_PARAM --block=dut --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "axi4_stream_channel.h"
#include "notify_ack_channel.h"
#include "pop_ack_channel.h"
#include "push_ack_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"
// GENERATED_CODE_END
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module pySocket_dut.block;
import pySocket_dut.base;
import pySocket_tb;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace pySocket_tb_ns;
export SC_MODULE(dut), public blockBase, public dutBase
{
private:

public:

    dut(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~dut() override = default;

    // GENERATED_CODE_END
    // block implementation members

    void dutListener(void);
    void dut2PythonListener(void);
    void pushPopListener(void);
    void notifyListener(void);
    void rdyVldListener(void);
    void axi4StreamListener(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(dut);

// === Block factory registration (dut) ===
void register_dut_variants() {
    instanceFactory::registerBlock("dut_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<dut>(blockName, variant, bbMode)); }, "", "pySocket");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _dut_registered = (register_dut_variants(), 0);
} // namespace
// === End block factory registration ===

dut::dut(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("dut", name(), bbMode)
        ,dutBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(dutListener);
    SC_THREAD(dut2PythonListener);
    SC_THREAD(pushPopListener);
    SC_THREAD(notifyListener);
    SC_THREAD(rdyVldListener);
    SC_THREAD(axi4StreamListener);
};

void dut::dutListener(void)
{
    log_.logPrint(std::format("started dutListener"), LOG_IMPORTANT );
    // Finite workload: pySocket.py sends two requests then shuts down the initiator socket.
    while (true) {
        p2s_message_st message;
        p2s_response_st response;
        test_req_ack->reqReceive(message);
        log_.logPrint(std::format("received message: {} {}", message.param1, message.param2), LOG_IMPORTANT );
        response.response = message.param1 + message.param2;
        test_req_ack->ack(response);
    }
}

void dut::dut2PythonListener(void)
{
    log_.logPrint(std::format("started dut2PythonListener"), LOG_IMPORTANT );
    constexpr uint32_t kDutPushPopCmd = 0x50555348u; // "PUSH"
    constexpr uint32_t kDutNotifyCmd = 0x4E4F5449u;  // "NOTI"
    constexpr uint32_t kDutRdyVldCmd = 0x52445956u;  // "RDYV"
    constexpr uint32_t kDutAxisCmd = 0x41584953u;    // "AXIS"
    while (true) {
        p2s_message_st test_message;
        p2s_response_st test_response;
        test2Python_req_ack->reqReceive(test_message);

        if (test_message.param1 == kDutPushPopCmd) {
            dut2Python_push_ack->push(test_message);
            p2s_response_st pop_data;
            dut2Python_pop_ack->pop(pop_data);
            test2Python_req_ack->ack(pop_data);
            continue;
        }
        if (test_message.param1 == kDutNotifyCmd) {
            dut2Python_notify_ack->notify();
            test_response.response = 0xA11Cu;
            test2Python_req_ack->ack(test_response);
            continue;
        }
        if (test_message.param1 == kDutRdyVldCmd) {
            dut2Python_rdy_vld->write(test_message);
            test_response.response = test_message.param1 + test_message.param2 + 2;
            test2Python_req_ack->ack(test_response);
            continue;
        }
        if (test_message.param1 == kDutAxisCmd) {
            axi4StreamInfoSt<p2s_message_st, axis_tid_st, axis_tdest_st> beat;
            beat.tdata = test_message;
            beat.tid.id = 0x1;
            beat.tdest.id = 0x2;
            beat.tlast = true;
            for (unsigned i = 0; i < beat.tstrb._byteWidth; ++i) {
                beat.tstrb[i] = Q_TRUE;
                beat.tkeep[i] = Q_TRUE;
            }
            dut2Python_axi4_stream->sendInfo(beat);
            test_response.response = test_message.param1 + test_message.param2 + 3;
            test2Python_req_ack->ack(test_response);
            continue;
        }

        p2s_response_st dut_response;
        dut2Python_req_ack->req(test_message, dut_response);

        test_response.response = dut_response.response;
        test2Python_req_ack->ack(test_response);
    }
}

void dut::pushPopListener(void)
{
    log_.logPrint(std::format("started pushPopListener"), LOG_IMPORTANT );
    while (true) {
        p2s_message_st message;
        test_push_ack->pushReceive(message);
        test_push_ack->ack();

        test_pop_ack->popReceive();
        p2s_response_st response;
        response.response = message.param1 + message.param2 + 1;
        test_pop_ack->ack(response);
    }
}

void dut::notifyListener(void)
{
    log_.logPrint(std::format("started notifyListener"), LOG_IMPORTANT );
    while (true) {
        test_notify_ack->waitNotify();
        test_notify_ack->ack();
    }
}

void dut::rdyVldListener(void)
{
    log_.logPrint(std::format("started rdyVldListener"), LOG_IMPORTANT );
    while (true) {
        p2s_message_st message;
        test_rdy_vld->read(message);
        log_.logPrint(std::format("received rdy_vld: {} {}", message.param1, message.param2), LOG_IMPORTANT );
    }
}

void dut::axi4StreamListener(void)
{
    log_.logPrint(std::format("started axi4StreamListener"), LOG_IMPORTANT );
    while (true) {
        axi4StreamInfoSt<p2s_message_st, axis_tid_st, axis_tdest_st> beat;
        test_axi4_stream->receiveInfo(beat);
        log_.logPrint(
            std::format("received axi4_stream: {} {} tlast={}",
                        beat.tdata.param1, beat.tdata.param2, beat.tlast),
            LOG_IMPORTANT);
    }
}

