//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=leafB --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "ahb_channel.h"
#include "addressMap.h"
#include "hwRegister.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module ahbDecode_leafB.block;
import ahbDecode_leafB.base;
import ahbDecode;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace ahbDecode_ns;
export SC_MODULE(leafB), public blockBase, public leafBBase
{
private:
    void regHandler(void);
    addressMap _a2cRegs;

public:

    //registers
    hwRegister< cfgRegSt, 4 > cfgB; // rw register

    leafB(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~leafB() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(leafB);

// === Block factory registration (leafB) ===
void register_leafB_variants() {
    instanceFactory::registerBlock("leafB_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<leafB>(blockName, variant, bbMode)); }, "", "ahbDecode");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _leafB_registered = (register_leafB_variants(), 0);
} // namespace
// === End block factory registration ===

void leafB::regHandler(void) { //handle register decode
    registerHandler< ahbAddrSt, ahbDataSt >(_a2cRegs, ahbReg, (1<<(3))-1, true); }

leafB::leafB(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("leafB", name(), bbMode)
        ,leafBBase(name(), variant)
        ,_a2cRegs(log_)
        ,cfgB(cfgRegSt::_packedSt(0x0))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // Generated register/memory address offsets
    constexpr uint64_t REG_ADDR_LEAFB_CFGB = 0x0;

    // register registers for FW access
    _a2cRegs.addRegister( REG_ADDR_LEAFB_CFGB, 4, "cfgB", &cfgB );
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
