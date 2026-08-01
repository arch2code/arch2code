//

// GENERATED_CODE_PARAM --block=pySocket --mode=module
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
#include <list>
#include <format>
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module pySocket.block;
import pySocket.base;
import pySocket_tb;
using namespace pySocket_tb_ns;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
export SC_MODULE(pySocket), public blockBase, public pySocketBase
{
private:

public:

    pySocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~pySocket() override = default;

    // GENERATED_CODE_END
    // block implementation members

    std::list<p2s_message_st> p2s_message_list;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(pySocket);

// === Block factory registration (pySocket) ===
void register_pySocket_variants() {
    instanceFactory::registerBlock("pySocket_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<pySocket>(blockName, variant, bbMode)); }, "", "pySocket");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _pySocket_registered = (register_pySocket_variants(), 0);
} // namespace
// === End block factory registration ===

pySocket::pySocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("pySocket", name(), bbMode)
        ,pySocketBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

