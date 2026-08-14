//

// GENERATED_CODE_PARAM --block=pySocket_tb --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "notify_ack_channel.h"
#include "pop_ack_channel.h"
#include "push_ack_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"
// GENERATED_CODE_END
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module pySocket_tb.block;
import pySocket_tb.base;
import pySocket_tb;
import pySocket.base;
import pySocket_dut.base;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace pySocket_tb_ns;
export SC_MODULE(pySocket_tb), public blockBase, public pySocket_tbBase
{
private:

public:
    // channels
    // Req Ack Test interface
    req_ack_channel< p2s_message_st, p2s_response_st > test_req_ack;
    // Req Ack Test2Python interface
    req_ack_channel< p2s_message_st, p2s_response_st > test2Python_req_ack;
    // Req Ack Dut2Python interface
    req_ack_channel< p2s_message_st, p2s_response_st > dut2Python_req_ack;
    // Python-initiated push into the DUT
    push_ack_channel< p2s_message_st > test_push_ack;
    // Python-initiated pop of data derived from the last push
    pop_ack_channel< p2s_response_st > test_pop_ack;
    // DUT-initiated push into Python
    push_ack_channel< p2s_message_st > dut2Python_push_ack;
    // DUT-initiated pop of data derived from the DUT push
    pop_ack_channel< p2s_response_st > dut2Python_pop_ack;
    // Python-initiated notify into the DUT
    notify_ack_channel< > test_notify_ack;
    // DUT-initiated notify into Python
    notify_ack_channel< > dut2Python_notify_ack;
    // Python-initiated rdy_vld write into the DUT
    rdy_vld_channel< p2s_message_st > test_rdy_vld;
    // DUT-initiated rdy_vld write into Python
    rdy_vld_channel< p2s_message_st > dut2Python_rdy_vld;

    //instances contained in block
    std::shared_ptr<pySocketBase> u_pySocket;
    std::shared_ptr<dutBase> u_dut;

    pySocket_tb(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~pySocket_tb() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(pySocket_tb);

// === Block factory registration (pySocket_tb) ===
void register_pySocket_tb_variants() {
    instanceFactory::registerBlock("pySocket_tb_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<pySocket_tb>(blockName, variant, bbMode)); }, "", "pySocket");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _pySocket_tb_registered = (register_pySocket_tb_variants(), 0);
} // namespace
// === End block factory registration ===

pySocket_tb::pySocket_tb(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("pySocket_tb", name(), bbMode)
        ,pySocket_tbBase(name(), variant)
        ,test_req_ack("dut_test_req_ack", "pySocket")
        ,test2Python_req_ack("dut_test2Python_req_ack", "pySocket")
        ,dut2Python_req_ack("pySocket_dut2Python_req_ack", "dut")
        ,test_push_ack("dut_test_push_ack", "pySocket")
        ,test_pop_ack("dut_test_pop_ack", "pySocket")
        ,dut2Python_push_ack("pySocket_dut2Python_push_ack", "dut")
        ,dut2Python_pop_ack("pySocket_dut2Python_pop_ack", "dut")
        ,test_notify_ack("dut_test_notify_ack", "pySocket")
        ,dut2Python_notify_ack("pySocket_dut2Python_notify_ack", "dut")
        ,test_rdy_vld("dut_test_rdy_vld", "pySocket")
        ,dut2Python_rdy_vld("pySocket_dut2Python_rdy_vld", "dut")
        ,u_pySocket(std::dynamic_pointer_cast<pySocketBase>(instanceFactory::createInstance(name(), "u_pySocket", "pySocket", "", "pySocket")))
        ,u_dut(std::dynamic_pointer_cast<dutBase>(instanceFactory::createInstance(name(), "u_dut", "dut", "", "pySocket")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    u_pySocket->test_req_ack(test_req_ack);
    u_dut->test_req_ack(test_req_ack);
    u_pySocket->test2Python_req_ack(test2Python_req_ack);
    u_dut->test2Python_req_ack(test2Python_req_ack);
    u_dut->dut2Python_req_ack(dut2Python_req_ack);
    u_pySocket->dut2Python_req_ack(dut2Python_req_ack);
    u_pySocket->test_push_ack(test_push_ack);
    u_dut->test_push_ack(test_push_ack);
    u_pySocket->test_pop_ack(test_pop_ack);
    u_dut->test_pop_ack(test_pop_ack);
    u_dut->dut2Python_push_ack(dut2Python_push_ack);
    u_pySocket->dut2Python_push_ack(dut2Python_push_ack);
    u_dut->dut2Python_pop_ack(dut2Python_pop_ack);
    u_pySocket->dut2Python_pop_ack(dut2Python_pop_ack);
    u_pySocket->test_notify_ack(test_notify_ack);
    u_dut->test_notify_ack(test_notify_ack);
    u_dut->dut2Python_notify_ack(dut2Python_notify_ack);
    u_pySocket->dut2Python_notify_ack(dut2Python_notify_ack);
    u_pySocket->test_rdy_vld(test_rdy_vld);
    u_dut->test_rdy_vld(test_rdy_vld);
    u_dut->dut2Python_rdy_vld(dut2Python_rdy_vld);
    u_pySocket->dut2Python_rdy_vld(dut2Python_rdy_vld);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

