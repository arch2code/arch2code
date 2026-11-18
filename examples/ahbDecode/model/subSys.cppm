//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=subSys --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "ahb_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module ahbDecode_subSys.block;
import ahbDecode_subSys.base;
import ahbDecode;
import ahbDecode_subRouter.base;
import ahbDecode_leafB.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace ahbDecode_ns;
export SC_MODULE(subSys), public blockBase, public subSysBase
{
private:

public:
    // channels
    // CPU access to the registers in the design
    ahb_channel< ahbAddrSt, ahbDataSt > ahbReg_uLeafC;

    //instances contained in block
    std::shared_ptr<subRouterBase> uSubRouter;
    std::shared_ptr<leafBBase> uLeafC;

    subSys(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~subSys() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(subSys);

// === Block factory registration (subSys) ===
void register_subSys_variants() {
    instanceFactory::registerBlock("subSys_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<subSys>(blockName, variant, bbMode)); }, "", "ahbDecode");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _subSys_registered = (register_subSys_variants(), 0);
} // namespace
// === End block factory registration ===

subSys::subSys(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("subSys", name(), bbMode)
        ,subSysBase(name(), variant)
        ,ahbReg_uLeafC("leafB_ahbReg_uLeafC", "subRouter")
        ,uSubRouter(std::dynamic_pointer_cast<subRouterBase>(instanceFactory::createInstance(name(), "uSubRouter", "subRouter", "", "ahbDecode")))
        ,uLeafC(std::dynamic_pointer_cast<leafBBase>(instanceFactory::createInstance(name(), "uLeafC", "leafB", "", "ahbDecode")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uSubRouter->ahbReg(ahbReg);
    // instance to instance connections via channel
    uSubRouter->ahbReg_uLeafC(ahbReg_uLeafC);
    uLeafC->ahbReg(ahbReg_uLeafC);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
