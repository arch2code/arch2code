//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=pySocket_tb
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "pySocket_tb.h"
import pySocket.base;
import dut.base;
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

