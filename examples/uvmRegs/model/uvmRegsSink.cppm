//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsSink --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "rdy_vld_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "testController.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module uvmRegs_uvmRegsSink.block;
import uvmRegs_uvmRegsSink.base;
import uvmRegs;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
import uvmRegs.uvmRegsStat.config;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmRegs_ns;
export SC_MODULE(uvmRegsSink), public blockBase, public uvmRegsSinkBase
{
private:

public:

    uvmRegsSink(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmRegsSink() override = default;

    // GENERATED_CODE_END
    // block implementation members

private:
    void stream_test(void);
    void endOfTestVoter(void);

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(uvmRegsSink);

// === Block factory registration (uvmRegsSink) ===
void register_uvmRegsSink_variants() {
    instanceFactory::registerBlock("uvmRegsSink_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmRegsSink>(blockName, variant, bbMode)); }, "", "uvmRegs");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmRegsSink_registered = (register_uvmRegsSink_variants(), 0);
} // namespace
// === End block factory registration ===

uvmRegsSink::uvmRegsSink(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmRegsSink", name(), bbMode)
        ,uvmRegsSinkBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    ADD_TEST(stream_test);
    SC_THREAD(endOfTestVoter);
};

// uDrv sends i * 7 for word i, and programs both offsets, tab row r to r
// times UVM_REGS_TB_TAB_STEP and mode.invert. uStat is variant v0, whose tab
// rows hold UVM_REGS_TAB_W bits.
void uvmRegsSink::stream_test(void)
{
    for (unsigned i = 0; i < UVM_REGS_WORDS; ++i) {
        uvmRegsWordSt w;
        in->read(w);
        uint16_t s = static_cast<uint16_t>(i * 7 + UVM_REGS_TB_OFFSET0 + UVM_REGS_TB_OFFSET1);
        constexpr uint64_t tabMask = (1ULL << uvmRegs_uvmRegsStatV0Config::UVM_REGS_TAB_W) - 1;
        uint16_t expected = static_cast<uint16_t>(~(s ^ (((s % UVM_REGS_TAB_ROWS) * UVM_REGS_TB_TAB_STEP) & tabMask)));
        if (w.word != expected) {
            errorCode::fail(std::format("{}: word {} is 0x{:x}, expected 0x{:x}", name(), i, (uint64_t)w.word, expected));
        }
    }
}

void uvmRegsSink::endOfTestVoter(void)
{
    endOfTest eot(true);
    testController::GetInstance().wait_all_tests_complete();
    eot.setEndOfTest(true);
}
