//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsDeep --mode=module
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
export module uvmRegs_uvmRegsDeep.block;
import uvmRegs_uvmRegsDeep.base;
import uvmRegs;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmRegs_ns;
export SC_MODULE(uvmRegsDeep), public blockBase, public uvmRegsDeepBase
{
private:
    void regHandler(void);
    addressMap _a2cRegs;

public:

    //registers
    hwRegister< uvmRegsIdentSt, 4, true > ident; // Fixed identifier
    hwRegister< uvmRegsByteSt, 4 > cfg; // Byte off the datapath

    uvmRegsDeep(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmRegsDeep() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(uvmRegsDeep);

// === Block factory registration (uvmRegsDeep) ===
void register_uvmRegsDeep_variants() {
    instanceFactory::registerBlock("uvmRegsDeep_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmRegsDeep>(blockName, variant, bbMode)); }, "", "uvmRegs");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmRegsDeep_registered = (register_uvmRegsDeep_variants(), 0);
} // namespace
// === End block factory registration ===

void uvmRegsDeep::regHandler(void) { //handle register decode
    registerHandler< uvmRegsAddrSt, uvmRegsDataSt >(_a2cRegs, apbReg, (1<<(4))-1); }

uvmRegsDeep::uvmRegsDeep(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmRegsDeep", name(), bbMode)
        ,uvmRegsDeepBase(name(), variant)
        ,_a2cRegs(log_)
        ,ident()
        ,cfg(uvmRegsByteSt::_packedSt(0x5a))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // Generated register/memory address offsets
    constexpr uint64_t REG_ADDR_UVMREGSDEEP_IDENT = 0x0;
    constexpr uint64_t REG_ADDR_UVMREGSDEEP_CFG = 0x8;

    // register registers for FW access
    _a2cRegs.addRegister( REG_ADDR_UVMREGSDEEP_IDENT, 2, "ident", &ident );
    _a2cRegs.addRegister( REG_ADDR_UVMREGSDEEP_CFG, 1, "cfg", &cfg );
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    uvmRegsIdentSt id;
    id.ident = UVM_REGS_IDENT;
    ident.write(id);
};
