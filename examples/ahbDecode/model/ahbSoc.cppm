//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ahbSoc --mode=module
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
export module ahbDecode_ahbSoc.block;
import ahbDecode_ahbSoc.base;
import ahbDecode;
import ahbDecode_ahbRouter.base;
import ahbDecode_leafA.base;
import ahbDecode_leafB.base;
import ahbDecode_subSys.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace ahbDecode_ns;
export SC_MODULE(ahbSoc), public blockBase, public ahbSocBase
{
private:

public:
    // channels
    // CPU access to the registers in the design
    ahb_channel< ahbAddrSt, ahbDataSt > ahbReg_uLeafA;
    // CPU access to the registers in the design
    ahb_channel< ahbAddrSt, ahbDataSt > ahbReg_uLeafB;
    // CPU access to the registers in the design
    ahb_channel< ahbAddrSt, ahbDataSt > ahbReg_uSubSys;

    //instances contained in block
    std::shared_ptr<ahbRouterBase> uRouter;
    std::shared_ptr<leafABase> uLeafA;
    std::shared_ptr<leafBBase> uLeafB;
    std::shared_ptr<subSysBase> uSubSys;

    ahbSoc(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ahbSoc() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(ahbSoc);

// === Block factory registration (ahbSoc) ===
void register_ahbSoc_variants() {
    instanceFactory::registerBlock("ahbSoc_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ahbSoc>(blockName, variant, bbMode)); }, "", "ahbDecode");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _ahbSoc_registered = (register_ahbSoc_variants(), 0);
} // namespace
// === End block factory registration ===

ahbSoc::ahbSoc(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ahbSoc", name(), bbMode)
        ,ahbSocBase(name(), variant)
        ,ahbReg_uLeafA("leafA_ahbReg_uLeafA", "ahbRouter")
        ,ahbReg_uLeafB("leafB_ahbReg_uLeafB", "ahbRouter")
        ,ahbReg_uSubSys("subSys_ahbReg_uSubSys", "ahbRouter")
        ,uRouter(std::dynamic_pointer_cast<ahbRouterBase>(instanceFactory::createInstance(name(), "uRouter", "ahbRouter", "", "ahbDecode")))
        ,uLeafA(std::dynamic_pointer_cast<leafABase>(instanceFactory::createInstance(name(), "uLeafA", "leafA", "", "ahbDecode")))
        ,uLeafB(std::dynamic_pointer_cast<leafBBase>(instanceFactory::createInstance(name(), "uLeafB", "leafB", "", "ahbDecode")))
        ,uSubSys(std::dynamic_pointer_cast<subSysBase>(instanceFactory::createInstance(name(), "uSubSys", "subSys", "", "ahbDecode")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uRouter->ahbReg(ahbReg);
    // instance to instance connections via channel
    uRouter->ahbReg_uLeafA(ahbReg_uLeafA);
    uLeafA->ahbReg(ahbReg_uLeafA);
    uRouter->ahbReg_uLeafB(ahbReg_uLeafB);
    uLeafB->ahbReg(ahbReg_uLeafB);
    uRouter->ahbReg_uSubSys(ahbReg_uSubSys);
    uSubSys->ahbReg(ahbReg_uSubSys);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
