//

// GENERATED_CODE_PARAM --block=xpMtxSrcPar --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "xpMtxIpVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "q_assert.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpMtxIp_xpMtxSrcPar.block;
import xpMtxIp_xpMtxSrcPar.base;
import xpMtxIp;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpMtxIp_ns;
export template<typename Config>
SC_MODULE(xpMtxSrcPar), public blockBase, public xpMtxSrcParBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpMtxSrcPar);

    // inherited names usable unqualified (no Config:: / this->)
    using xpMtxSrcParBase<Config>::MI_SRC_WIDTH;
    using xpMtxSrcParBase<Config>::out;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpMtxSrcParBase<Config>::miSrcPixelT;
    using typename xpMtxSrcParBase<Config>::miSrcParSt;

    xpMtxSrcPar(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpMtxSrcPar() override = default;

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
template<typename Config>
xpMtxSrcPar<Config>::xpMtxSrcPar(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpMtxSrcPar", name(), bbMode)
        ,xpMtxSrcParBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(drive);
};

// Drives four samples with a distinct value in every field of every sample.
// The bound width is asserted so a parameter that stops reaching this block
// fails loud rather than silently resolving to the declared default.
template<typename Config>
void xpMtxSrcPar<Config>::drive(void)
{
    Q_ASSERT(MI_SRC_WIDTH == 12, "xpMtxSrcPar MI_SRC_WIDTH must resolve to the bound value 12");
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        miSrcParSt sample{};
        sample.tag  = FIRST_TAG + i;
        sample.data = FIRST_DATA + i;
        sample.mark = FIRST_MARK + i;
        out->push(sample);
        log_.logPrint(std::format("{} drove tag {} data 0x{:x} mark 0x{:x}", this->name(),
            (uint64_t)sample.tag, (uint64_t)sample.data, (uint64_t)sample.mark), LOG_IMPORTANT);
    }
}

