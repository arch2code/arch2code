//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegs --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "apb_channel.h"
#include "rdy_vld_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module uvmRegs.block;
import uvmRegs.base;
import uvmRegs.uvmRegsScale.config;
import uvmRegs.uvmRegsStat.config;
import uvmRegs;
import uvmRegs_uvmRegsRouter.base;
import uvmRegs_uvmRegsScale.base;
import uvmRegs_uvmRegsStat.base;
import uvmRegs_uvmRegsBridge.base;
import uvmRegs_uvmRegsWrap.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmRegs_ns;
export SC_MODULE(uvmRegs), public blockBase, public uvmRegsBase
{
private:

public:
    // channels
    // Datapath words
    rdy_vld_channel< uvmRegsWordSt > scaled0;
    // Datapath words
    rdy_vld_channel< uvmRegsWordSt > scaled1;
    // Register bus
    apb_channel< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uScale0;
    // Register bus
    apb_channel< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uScale1;
    // Register bus
    apb_channel< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uStat;
    // Register bus
    apb_channel< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uWrap;
    // Register bus
    apb_channel< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uBridge;

    //instances contained in block
    std::shared_ptr<uvmRegsRouterBase> uRouter;
    std::shared_ptr<uvmRegsScaleBase<uvmRegs_uvmRegsScaleV0Config>> uScale0;
    std::shared_ptr<uvmRegsScaleBase<uvmRegs_uvmRegsScaleV1Config>> uScale1;
    std::shared_ptr<uvmRegsStatBase<uvmRegs_uvmRegsStatV0Config>> uStat;
    std::shared_ptr<uvmRegsBridgeBase> uBridge;
    std::shared_ptr<uvmRegsWrapBase> uWrap;

    uvmRegs(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmRegs() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(uvmRegs);

// === Block factory registration (uvmRegs) ===
void register_uvmRegs_variants() {
    instanceFactory::registerBlock("uvmRegs_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmRegs>(blockName, variant, bbMode)); }, "", "uvmRegs");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmRegs_registered = (register_uvmRegs_variants(), 0);
} // namespace
// === End block factory registration ===

uvmRegs::uvmRegs(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmRegs", name(), bbMode)
        ,uvmRegsBase(name(), variant)
        ,scaled0("uvmRegsScale_scaled0", "uvmRegsScale", BACKPRESSURE_ALLOWED)
        ,scaled1("uvmRegsStat_scaled1", "uvmRegsScale", BACKPRESSURE_ALLOWED)
        ,apbReg_uScale0("uvmRegsScale_apbReg_uScale0", "uvmRegsRouter")
        ,apbReg_uScale1("uvmRegsScale_apbReg_uScale1", "uvmRegsRouter")
        ,apbReg_uStat("uvmRegsStat_apbReg_uStat", "uvmRegsRouter")
        ,apbReg_uWrap("uvmRegsWrap_apbReg_uWrap", "uvmRegsRouter")
        ,apbReg_uBridge("uvmRegsBridge_apbReg_uBridge", "uvmRegsRouter")
        ,uRouter(std::dynamic_pointer_cast<uvmRegsRouterBase>(instanceFactory::createInstance(name(), "uRouter", "uvmRegsRouter", "", "uvmRegs")))
        ,uScale0(std::dynamic_pointer_cast<uvmRegsScaleBase<uvmRegs_uvmRegsScaleV0Config>>(instanceFactory::createInstance(name(), "uScale0", "uvmRegsScale", "v0", "uvmRegs.uvmRegs.uvmRegs_uvmRegsScale")))
        ,uScale1(std::dynamic_pointer_cast<uvmRegsScaleBase<uvmRegs_uvmRegsScaleV1Config>>(instanceFactory::createInstance(name(), "uScale1", "uvmRegsScale", "v1", "uvmRegs.uvmRegs.uvmRegs_uvmRegsScale")))
        ,uStat(std::dynamic_pointer_cast<uvmRegsStatBase<uvmRegs_uvmRegsStatV0Config>>(instanceFactory::createInstance(name(), "uStat", "uvmRegsStat", "v0", "uvmRegs.uvmRegs.uvmRegs_uvmRegsStat")))
        ,uBridge(std::dynamic_pointer_cast<uvmRegsBridgeBase>(instanceFactory::createInstance(name(), "uBridge", "uvmRegsBridge", "", "uvmRegs")))
        ,uWrap(std::dynamic_pointer_cast<uvmRegsWrapBase>(instanceFactory::createInstance(name(), "uWrap", "uvmRegsWrap", "", "uvmRegs")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uScale0->in(in);
    uStat->out(out);
    uRouter->apbReg(apbReg);
    // instance to instance connections via channel
    uScale0->out(scaled0);
    uScale1->in(scaled0);
    uScale1->out(scaled1);
    uStat->in(scaled1);
    uRouter->apbReg_uScale0(apbReg_uScale0);
    uScale0->apbReg(apbReg_uScale0);
    uRouter->apbReg_uScale1(apbReg_uScale1);
    uScale1->apbReg(apbReg_uScale1);
    uRouter->apbReg_uStat(apbReg_uStat);
    uStat->apbReg(apbReg_uStat);
    uRouter->apbReg_uWrap(apbReg_uWrap);
    uWrap->apbReg(apbReg_uWrap);
    uRouter->apbReg_uBridge(apbReg_uBridge);
    uBridge->apbReg(apbReg_uBridge);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
