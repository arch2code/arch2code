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
#include "req_ack_channel.h"
// GENERATED_CODE_END
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module pySocket_dut.block;
import pySocket_dut.base;
import pySocket_tb;
using namespace pySocket_tb_ns;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
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
    // Two rounds to match pySocket.py (systemc2python_test + dut2python_target replies).
    while (true) {
        p2s_message_st test_message;
        p2s_response_st test_response;
        // wait for a request from the test code
        test2Python_req_ack->reqReceive(test_message);

        // make a request to the python code
        p2s_response_st dut_response;
        dut2Python_req_ack->req(test_message, dut_response);

        // send the response back to the test code
        test_response.response = dut_response.response;
        test2Python_req_ack->ack(test_response);
    }
}

