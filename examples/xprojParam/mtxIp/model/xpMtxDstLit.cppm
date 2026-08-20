//

// GENERATED_CODE_PARAM --block=xpMtxDstLit --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "q_assert.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpMtxIp_xpMtxDstLit.block;
import xpMtxIp_xpMtxDstLit.base;
import xpMtxIp;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpMtxIp_ns;
export SC_MODULE(xpMtxDstLit), public blockBase, public xpMtxDstLitBase
{
private:

public:

    xpMtxDstLit(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpMtxDstLit() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // The producer's sample count and field bases; every field of every sample
    // is checked, so a positional adapter that copied the wrong field or the
    // wrong number of bits fails here rather than delivering a plausible value.
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_TAG = 0;
    static constexpr uint32_t FIRST_DATA = 0xA10;
    static constexpr uint32_t FIRST_MARK = 0x50;
    void check(void);
    endOfTest m_eot;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpMtxDstLit);

// === Block factory registration (xpMtxDstLit) ===
void register_xpMtxDstLit_variants() {
    instanceFactory::registerBlock("xpMtxDstLit_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpMtxDstLit>(blockName, variant, bbMode)); }, "", "xpMtxIp");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpMtxDstLit_registered = (register_xpMtxDstLit_variants(), 0);
} // namespace
// === End block factory registration ===

xpMtxDstLit::xpMtxDstLit(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpMtxDstLit", name(), bbMode)
        ,xpMtxDstLitBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(check);
};

// Checks every field of every sample, then votes the test done.
void xpMtxDstLit::check(void)
{
    m_eot.registerVoter();
    miDstLitSt sample{};
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        in->pushReceive(sample);
        in->ack();
        log_.logPrint(std::format("{} received tag {} data 0x{:x} mark 0x{:x}", this->name(),
            (uint64_t)sample.tag, (uint64_t)sample.data, (uint64_t)sample.mark), LOG_IMPORTANT);
        Q_ASSERT((uint64_t)sample.tag  == FIRST_TAG + i,  "xpMtxDstLit tag field mismatch");
        Q_ASSERT((uint64_t)sample.data == FIRST_DATA + i, "xpMtxDstLit data field mismatch");
        Q_ASSERT((uint64_t)sample.mark == FIRST_MARK + i, "xpMtxDstLit mark field mismatch");
    }
    log_.logPrint(std::format("{} checked {} samples", this->name(), SAMPLE_COUNT), LOG_IMPORTANT);
    m_eot.setEndOfTest(true);
}

