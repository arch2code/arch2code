//

// GENERATED_CODE_PARAM --block=axiSocketSlave_tb --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "axi_read_channel.h"
#include "axi_write_channel.h"
// GENERATED_CODE_END
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module axiSocketSlave_tb.block;
import axiSocketSlave_tb.base;
import axiSocketSlave_tb;
import axiSocketSlave_producer.base;
import axiSocketSlave_axiSocket.base;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace axiSocketSlave_tb_ns;
export SC_MODULE(axiSocketSlave_tb), public blockBase, public axiSocketSlave_tbBase
{
private:

public:
    // channels
    // AXI Read channels; Address and Data
    axi_read_channel< axiAddrSt, axiDataSt > axiRd0;
    // AXI Write channels; Address, Data, and Response
    axi_write_channel< axiAddrSt, axiDataSt, axiStrobeSt > axiWr0;

    //instances contained in block
    std::shared_ptr<producerBase> u_producer;
    std::shared_ptr<axiSocketBase> u_axiSocket;

    axiSocketSlave_tb(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axiSocketSlave_tb() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(axiSocketSlave_tb);

// === Block factory registration (axiSocketSlave_tb) ===
void register_axiSocketSlave_tb_variants() {
    instanceFactory::registerBlock("axiSocketSlave_tb_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<axiSocketSlave_tb>(blockName, variant, bbMode)); }, "", "axiSocketSlave");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _axiSocketSlave_tb_registered = (register_axiSocketSlave_tb_variants(), 0);
} // namespace
// === End block factory registration ===

axiSocketSlave_tb::axiSocketSlave_tb(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("axiSocketSlave_tb", name(), bbMode)
        ,axiSocketSlave_tbBase(name(), variant)
        ,axiRd0("axiSocket_axiRd0", "producer", "api_list_size", 256, "")
        ,axiWr0("axiSocket_axiWr0", "producer", "api_list_size", 256, "")
        ,u_producer(std::dynamic_pointer_cast<producerBase>(instanceFactory::createInstance(name(), "u_producer", "producer", "", "axiSocketSlave")))
        ,u_axiSocket(std::dynamic_pointer_cast<axiSocketBase>(instanceFactory::createInstance(name(), "u_axiSocket", "axiSocket", "", "axiSocketSlave")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    u_producer->axiRd0(axiRd0);
    u_axiSocket->axiRd0(axiRd0);
    u_producer->axiWr0(axiWr0);
    u_axiSocket->axiWr0(axiWr0);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

