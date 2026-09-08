//

// GENERATED_CODE_PARAM --block=xpCstSharedChk --mode=module
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
export module xpCstShared_xpCstSharedChk.block;
import xpCstShared_xpCstSharedChk.base;
import xpCstShared.xpCstSharedChk.config;
import xpCstShared_xpCstSharedDefs;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpCstShared_xpCstSharedDefs_ns;
export template<typename Config>
SC_MODULE(xpCstSharedChk), public blockBase, public xpCstSharedChkBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpCstSharedChk);

    // inherited names usable unqualified (no Config:: / this->)
    using xpCstSharedChkBase<Config>::CSH_WIDTH;
    using xpCstSharedChkBase<Config>::in;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpCstSharedChkBase<Config>::cshPixelT;
    using typename xpCstSharedChkBase<Config>::cshSt;

    xpCstSharedChk(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpCstSharedChk() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // The value the top binds, restated independently of the YAML so the assertion is a real check.
    static constexpr uint32_t BOUND_WIDTH = 12;
    // Mirror of the producer's field bases.
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_TAG = 0;
    static constexpr uint32_t FIRST_DATA = 0xA10;
    static constexpr uint32_t FIRST_MARK = 0x50;
    void check(void);
    endOfTest m_eot;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpCstSharedChk<Config>::xpCstSharedChk(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpCstSharedChk", name(), bbMode)
        ,xpCstSharedChkBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(check);
};

template<typename Config>
void xpCstSharedChk<Config>::check(void)
{
    Q_ASSERT(CSH_WIDTH == BOUND_WIDTH,
        std::format("xpCstSharedChk must resolve CSH_WIDTH to {} but resolved {}",
            BOUND_WIDTH, (uint64_t)CSH_WIDTH));
    m_eot.registerVoter();
    cshSt sample{};
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        in->pushReceive(sample);
        in->ack();
        log_.logPrint(std::format("{} received tag {} data 0x{:x} mark 0x{:x}", this->name(),
            (uint64_t)sample.tag, (uint64_t)sample.data, (uint64_t)sample.mark),
            LOG_IMPORTANT);
        Q_ASSERT((uint64_t)sample.tag  == FIRST_TAG + i, "xpCstSharedChk tag field mismatch");
        Q_ASSERT((uint64_t)sample.data == FIRST_DATA + i, "xpCstSharedChk data field mismatch");
        Q_ASSERT((uint64_t)sample.mark == FIRST_MARK + i, "xpCstSharedChk mark field mismatch");
    }
    log_.logPrint(std::format("{} checked {} samples at pixel width {}", this->name(),
        SAMPLE_COUNT, (uint64_t)CSH_WIDTH), LOG_IMPORTANT);
    m_eot.setEndOfTest(true);
}

