//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmMemSink --mode=module
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
export module uvmMem_uvmMemSink.block;
import uvmMem_uvmMemSink.base;
import uvmMem;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmMem_ns;
export SC_MODULE(uvmMemSink), public blockBase, public uvmMemSinkBase
{
private:

public:

    uvmMemSink(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmMemSink() override = default;

    // GENERATED_CODE_END
    // block implementation members

private:
    void copy_test(void);
    void endOfTestVoter(void);
    void statusPrint(void);
    unsigned checked_ = 0;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(uvmMemSink);

// === Block factory registration (uvmMemSink) ===
void register_uvmMemSink_variants() {
    instanceFactory::registerBlock("uvmMemSink_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmMemSink>(blockName, variant, bbMode)); }, "", "uvmMem");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmMemSink_registered = (register_uvmMemSink_variants(), 0);
} // namespace
// === End block factory registration ===

uvmMemSink::uvmMemSink(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmMemSink", name(), bbMode)
        ,uvmMemSinkBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    logging::GetInstance().registerStatus(name(), [this](void){ statusPrint(); });
    ADD_TEST(copy_test);
    SC_THREAD(endOfTestVoter);
};

// Command i reads the word command i - 1 wrote; command 0 reads a word
// nothing wrote, which uStore holds at zero.
void uvmMemSink::copy_test(void)
{
    for (checked_ = 0; checked_ < UVM_MEM_CMDS; ++checked_) {
        uvmMemWordSt w;
        in->read(w);
        uvmMemDataT expected = checked_ == 0 ? 0 : static_cast<uvmMemDataT>(UVM_MEM_DATA_BASE + checked_ - 1);
        if (w.word != expected) {
            errorCode::fail(std::format("{}: word {} is 0x{:x}, expected 0x{:x}", name(), checked_, (uint64_t)w.word, (uint64_t)expected));
        }
    }
    log_.logPrint(std::format("{} checked {} words", name(), UVM_MEM_CMDS), LOG_IMPORTANT);
}

void uvmMemSink::endOfTestVoter(void)
{
    endOfTest eot(true);
    testController::GetInstance().wait_all_tests_complete();
    eot.setEndOfTest(true);
}

void uvmMemSink::statusPrint(void)
{
    log_.logPrint(std::format("{} of {} words checked", checked_, UVM_MEM_CMDS), LOG_IMPORTANT);
}
