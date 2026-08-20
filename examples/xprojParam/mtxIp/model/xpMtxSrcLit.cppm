//

// GENERATED_CODE_PARAM --block=xpMtxSrcLit --mode=module
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
export module xpMtxIp_xpMtxSrcLit.block;
import xpMtxIp_xpMtxSrcLit.base;
import xpMtxIp;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpMtxIp_ns;
export SC_MODULE(xpMtxSrcLit), public blockBase, public xpMtxSrcLitBase
{
private:

public:

    xpMtxSrcLit(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpMtxSrcLit() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // Sample count and the first value driven on each payload field. The pixel
    // is 12 bits with a non-zero high nibble, so a byte-wide truncating copy
    // shows up as a mismatch; the marker sits above it, so a wrong-width pixel
    // shifts the marker rather than passing silently.
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_TAG = 0;
    static constexpr uint32_t FIRST_DATA = 0xA10;
    static constexpr uint32_t FIRST_MARK = 0x50;
    void drive(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpMtxSrcLit);

// === Block factory registration (xpMtxSrcLit) ===
void register_xpMtxSrcLit_variants() {
    instanceFactory::registerBlock("xpMtxSrcLit_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpMtxSrcLit>(blockName, variant, bbMode)); }, "", "xpMtxIp");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpMtxSrcLit_registered = (register_xpMtxSrcLit_variants(), 0);
} // namespace
// === End block factory registration ===

xpMtxSrcLit::xpMtxSrcLit(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpMtxSrcLit", name(), bbMode)
        ,xpMtxSrcLitBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(drive);
};

// Drives four samples with a distinct value in every field of every sample.
void xpMtxSrcLit::drive(void)
{
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        miSrcLitSt sample{};
        sample.tag  = FIRST_TAG + i;
        sample.data = FIRST_DATA + i;
        sample.mark = FIRST_MARK + i;
        out->push(sample);
        log_.logPrint(std::format("{} drove tag {} data 0x{:x} mark 0x{:x}", this->name(),
            (uint64_t)sample.tag, (uint64_t)sample.data, (uint64_t)sample.mark), LOG_IMPORTANT);
    }
}

