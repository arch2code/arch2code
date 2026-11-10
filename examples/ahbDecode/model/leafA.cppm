//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=leafA --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "ahb_channel.h"
#include "addressMap.h"
#include "hwRegister.h"
#include "hwMemory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module ahbDecode_leafA.block;
import ahbDecode_leafA.base;
import ahbDecode;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace ahbDecode_ns;
export SC_MODULE(leafA), public blockBase, public leafABase
{
private:
    void regHandler(void);
    addressMap _a2cRegs;

public:

    //registers
    hwRegister< cfgRegSt, 4 > cfgA; // rw register
    hwRegister< statRegSt, 4, true > statA; // ro register, reads 0x5a5a
    hwRegister< cmdRegSt, 4 > cmdA; // ext register whose owner refuses a write of 0x0bad

    memories mems;
    //memories
    hwMemory< tblSt > tblA;

    leafA(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~leafA() override = default;
    void setTimed(int nsec, timedDelayMode mode) override
    {
        leafABase::setTimed(nsec, mode);
        mems.setTimed(nsec, mode);
    }

    // GENERATED_CODE_END
    // block implementation members

private:
    void init(void);
    cmdRegSt m_cmdAccepted;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(leafA);

// === Block factory registration (leafA) ===
void register_leafA_variants() {
    instanceFactory::registerBlock("leafA_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<leafA>(blockName, variant, bbMode)); }, "", "ahbDecode");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _leafA_registered = (register_leafA_variants(), 0);
} // namespace
// === End block factory registration ===

void leafA::regHandler(void) { //handle register decode
    registerHandler< ahbAddrSt, ahbDataSt >(_a2cRegs, ahbReg, (1<<(6))-1, true); }

leafA::leafA(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("leafA", name(), bbMode)
        ,leafABase(name(), variant)
        ,_a2cRegs(log_)
        ,cfgA(cfgRegSt::_packedSt(0x12345678))
        ,statA()
        ,cmdA()
        ,tblA(name(), "tblA", mems, TBL_WORDS)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // Generated register/memory address offsets
    constexpr uint64_t REG_ADDR_LEAFA_TBLA = 0x0;
    constexpr uint64_t REG_ADDR_LEAFA_CFGA = 0x20;
    constexpr uint64_t REG_ADDR_LEAFA_STATA = 0x28;
    constexpr uint64_t REG_ADDR_LEAFA_CMDA = 0x30;

    // register memories for FW access
    _a2cRegs.addMemory( REG_ADDR_LEAFA_TBLA, tblSt::_byteWidth, TBL_WORDS, std::string(this->name()) + ".tblA", &tblA);
    // register registers for FW access
    _a2cRegs.addRegister( REG_ADDR_LEAFA_CFGA, 4, "cfgA", &cfgA );
    _a2cRegs.addRegister( REG_ADDR_LEAFA_STATA, 2, "statA", &statA );
    _a2cRegs.addRegister( REG_ADDR_LEAFA_CMDA, 2, "cmdA", &cmdA );
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    // The owner of cmdA refuses 0x0bad and keeps the value it last accepted,
    // as rtl/leafA.sv does.
    cmdA.setWriteErrorHandler([this](uint64_t, uint32_t val) {
        if (val == 0x0bad) {
            cmdA.write(m_cmdAccepted);
            return true;
        }
        m_cmdAccepted = cmdA.read();
        return false;
    });
    SC_THREAD(init);
};

// Reset values the RTL drives
void leafA::init(void)
{
    statRegSt stat;
    stat.value = 0x5a5a;
    statA.write(stat);
    m_cmdAccepted.value = 0x0c0d;
    cmdA.write(m_cmdAccepted);
}
