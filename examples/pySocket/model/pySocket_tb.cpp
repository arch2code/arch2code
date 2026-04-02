//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=pySocket_tb
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "pySocket_tb.h"
#include "pySocketBase.h"
#include "dutBase.h"
SC_HAS_PROCESS(pySocket_tb);

pySocket_tb::registerBlock pySocket_tb::registerBlock_; //register the block with the factory

pySocket_tb::pySocket_tb(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("pySocket_tb", name(), bbMode)
        ,pySocket_tbBase(name(), variant)
        ,test_req_ack("dut_test_req_ack", "pySocket")
        ,u_pySocket(std::dynamic_pointer_cast<pySocketBase>( instanceFactory::createInstance(name(), "u_pySocket", "pySocket", "")))
        ,u_dut(std::dynamic_pointer_cast<dutBase>( instanceFactory::createInstance(name(), "u_dut", "dut", "")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    u_pySocket->test_req_ack(test_req_ack);
    u_dut->test_req_ack(test_req_ack);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

