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
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

