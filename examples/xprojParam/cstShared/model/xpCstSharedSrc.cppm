//

// GENERATED_CODE_PARAM --block=xpCstSharedSrc --mode=module
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
export module xpCstShared_xpCstSharedSrc.block;
import xpCstShared_xpCstSharedSrc.base;
import xpCstShared.xpCstSharedSrc.config;
import xpCstShared_xpCstSharedDefs;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpCstShared_xpCstSharedDefs_ns;
export template<typename Config>
SC_MODULE(xpCstSharedSrc), public blockBase, public xpCstSharedSrcBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpCstSharedSrc);

    // inherited names usable unqualified (no Config:: / this->)
    using xpCstSharedSrcBase<Config>::CSH_WIDTH;
    using xpCstSharedSrcBase<Config>::out;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpCstSharedSrcBase<Config>::cshPixelT;
    using typename xpCstSharedSrcBase<Config>::cshSt;

    xpCstSharedSrc(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpCstSharedSrc() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // The value the top binds, restated independently of the YAML so the assertion is a real check.
    static constexpr uint32_t BOUND_WIDTH = 12;
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_TAG = 0;
    static constexpr uint32_t FIRST_DATA = 0xA10;
    static constexpr uint32_t FIRST_MARK = 0x50;
    void drive(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpCstSharedSrc<Config>::xpCstSharedSrc(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpCstSharedSrc", name(), bbMode)
        ,xpCstSharedSrcBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(drive);
};

template<typename Config>
void xpCstSharedSrc<Config>::drive(void)
{
    Q_ASSERT(CSH_WIDTH == BOUND_WIDTH,
        std::format("xpCstSharedSrc must resolve CSH_WIDTH to {} but resolved {}",
            BOUND_WIDTH, (uint64_t)CSH_WIDTH));
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        cshSt sample{};
        sample.tag  = FIRST_TAG + i;
        sample.data = FIRST_DATA + i;
        sample.mark = FIRST_MARK + i;
        out->push(sample);
        log_.logPrint(std::format("{} drove tag {} data 0x{:x} mark 0x{:x}", this->name(),
            (uint64_t)sample.tag, (uint64_t)sample.data, (uint64_t)sample.mark),
            LOG_IMPORTANT);
    }
}

