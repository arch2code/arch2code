//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsBridge --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "apb_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module uvmRegs_uvmRegsBridge.block;
import uvmRegs_uvmRegsBridge.base;
import uvmRegs;
import uvmRegs_uvmRegsBridgeRouter.base;
import uvmRegs_uvmRegsDeep.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmRegs_ns;
export SC_MODULE(uvmRegsBridge), public blockBase, public uvmRegsBridgeBase
{
private:

public:
    // channels
    // Register bus
    apb_channel< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uDeep;

    //instances contained in block
    std::shared_ptr<uvmRegsBridgeRouterBase> uBridgeRouter;
    std::shared_ptr<uvmRegsDeepBase> uDeep;

    uvmRegsBridge(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmRegsBridge() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(uvmRegsBridge);

// === Block factory registration (uvmRegsBridge) ===
void register_uvmRegsBridge_variants() {
    instanceFactory::registerBlock("uvmRegsBridge_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmRegsBridge>(blockName, variant, bbMode)); }, "", "uvmRegs");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmRegsBridge_registered = (register_uvmRegsBridge_variants(), 0);
} // namespace
// === End block factory registration ===

uvmRegsBridge::uvmRegsBridge(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmRegsBridge", name(), bbMode)
        ,uvmRegsBridgeBase(name(), variant)
        ,apbReg_uDeep("uvmRegsDeep_apbReg_uDeep", "uvmRegsBridgeRouter")
        ,uBridgeRouter(std::dynamic_pointer_cast<uvmRegsBridgeRouterBase>(instanceFactory::createInstance(name(), "uBridgeRouter", "uvmRegsBridgeRouter", "", "uvmRegs")))
        ,uDeep(std::dynamic_pointer_cast<uvmRegsDeepBase>(instanceFactory::createInstance(name(), "uDeep", "uvmRegsDeep", "", "uvmRegs")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uBridgeRouter->apbReg(apbReg);
    // instance to instance connections via channel
    uBridgeRouter->apbReg_uDeep(apbReg_uDeep);
    uDeep->apbReg(apbReg_uDeep);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
