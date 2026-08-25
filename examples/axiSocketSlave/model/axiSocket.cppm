//

// GENERATED_CODE_PARAM --block=axiSocket --mode=module
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
export module axiSocketSlave_axiSocket.block;
import axiSocketSlave_axiSocket.base;
import axiSocketSlave_tb;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace axiSocketSlave_tb_ns;
export SC_MODULE(axiSocket), public blockBase, public axiSocketBase
{
private:

public:

    axiSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~axiSocket() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(axiSocket);

// === Block factory registration (axiSocket) ===
void register_axiSocket_variants() {
    instanceFactory::registerBlock("axiSocket_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<axiSocket>(blockName, variant, bbMode)); }, "", "axiSocketSlave");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _axiSocket_registered = (register_axiSocket_variants(), 0);
} // namespace
// === End block factory registration ===

axiSocket::axiSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("axiSocket", name(), bbMode)
        ,axiSocketBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

