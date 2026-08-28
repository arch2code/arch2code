//

// GENERATED_CODE_PARAM --block=axiSocketMaster_tb --mode=module
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
export module axiSocketMaster_tb.block;
import axiSocketMaster_tb.base;
import axiSocketMaster_tb;
import axiSocketMaster_axiSocket.base;
import axiSocketMaster_consumer.base;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace axiSocketMaster_tb_ns;
export SC_MODULE(axiSocketMaster_tb), public blockBase, public axiSocketMaster_tbBase
{
private:

public:
    // channels
    // AXI Read channels; Address and Data
    axi_read_channel< axiAddrSt, axiDataSt > axiRd0;
    // AXI Write channels; Address, Data, and Response
    axi_write_channel< axiAddrSt, axiDataSt, axiStrobeSt > axiWr0;

    //instances contained in block
    std::shared_ptr<axiSocketBase> u_axiSocket;
    std::shared_ptr<consumerBase> u_consumer;

    axiSocketMaster_tb(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axiSocketMaster_tb() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(axiSocketMaster_tb);

// === Block factory registration (axiSocketMaster_tb) ===
void register_axiSocketMaster_tb_variants() {
    instanceFactory::registerBlock("axiSocketMaster_tb_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<axiSocketMaster_tb>(blockName, variant, bbMode)); }, "", "axiSocketMaster");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _axiSocketMaster_tb_registered = (register_axiSocketMaster_tb_variants(), 0);
} // namespace
// === End block factory registration ===

axiSocketMaster_tb::axiSocketMaster_tb(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("axiSocketMaster_tb", name(), bbMode)
        ,axiSocketMaster_tbBase(name(), variant)
        ,axiRd0("consumer_axiRd0", "axiSocket", "api_list_size", 256, "")
        ,axiWr0("consumer_axiWr0", "axiSocket", "api_list_size", 256, "")
        ,u_axiSocket(std::dynamic_pointer_cast<axiSocketBase>(instanceFactory::createInstance(name(), "u_axiSocket", "axiSocket", "", "axiSocketMaster")))
        ,u_consumer(std::dynamic_pointer_cast<consumerBase>(instanceFactory::createInstance(name(), "u_consumer", "consumer", "", "axiSocketMaster")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    u_axiSocket->axiRd0(axiRd0);
    u_consumer->axiRd0(axiRd0);
    u_axiSocket->axiWr0(axiWr0);
    u_consumer->axiWr0(axiWr0);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

