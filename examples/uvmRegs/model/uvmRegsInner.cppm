//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsInner --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "apb_channel.h"
#include "addressMap.h"
#include "hwRegister.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module uvmRegs_uvmRegsInner.block;
import uvmRegs_uvmRegsInner.base;
import uvmRegs;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmRegs_ns;
export SC_MODULE(uvmRegsInner), public blockBase, public uvmRegsInnerBase
{
private:
    void regHandler(void);
    addressMap _a2cRegs;

public:

    //registers
    hwRegister< uvmRegsByteSt, 4 > tag; // Byte off the datapath

    uvmRegsInner(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmRegsInner() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(uvmRegsInner);

// === Block factory registration (uvmRegsInner) ===
void register_uvmRegsInner_variants() {
    instanceFactory::registerBlock("uvmRegsInner_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmRegsInner>(blockName, variant, bbMode)); }, "", "uvmRegs");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmRegsInner_registered = (register_uvmRegsInner_variants(), 0);
} // namespace
// === End block factory registration ===

void uvmRegsInner::regHandler(void) { //handle register decode
    registerHandler< uvmRegsAddrSt, uvmRegsDataSt >(_a2cRegs, apbReg, (1<<(3))-1); }

uvmRegsInner::uvmRegsInner(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmRegsInner", name(), bbMode)
        ,uvmRegsInnerBase(name(), variant)
        ,_a2cRegs(log_)
        ,tag(uvmRegsByteSt::_packedSt(0x11))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // Generated register/memory address offsets
    constexpr uint64_t REG_ADDR_UVMREGSINNER_TAG = 0x0;

    // register registers for FW access
    _a2cRegs.addRegister( REG_ADDR_UVMREGSINNER_TAG, 1, "tag", &tag );
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
