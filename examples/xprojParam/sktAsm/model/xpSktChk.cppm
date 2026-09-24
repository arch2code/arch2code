//

// GENERATED_CODE_PARAM --block=xpSktChk --mode=module
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
export module xpSktAsm_xpSktChk.block;
import xpSktAsm_xpSktChk.base;
import xpSktAsm.xpSktChk.config;
import xpSktIp;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpSktIp_ns;
export template<typename Config>
SC_MODULE(xpSktChk), public blockBase, public xpSktChkBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpSktChk);

    // inherited names usable unqualified (no Config:: / this->)
    using xpSktChkBase<Config>::SK_PIXEL_WIDTH;
    using xpSktChkBase<Config>::in;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpSktChkBase<Config>::skPixelT;
    using typename xpSktChkBase<Config>::skSampleSt;

    xpSktChk(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpSktChk() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // Python pushes SAMPLE_COUNT samples, tag = i and data = FIRST_PIXEL + i.
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_PIXEL = 0x10;
    static constexpr uint32_t ASM_WIDTH = 12;
    void check(void);
    endOfTest m_eot;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpSktChk<Config>::xpSktChk(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpSktChk", name(), bbMode)
        ,xpSktChkBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(check);
};

// The width assertion pins the assembler's own variant: the leaf feeding this
// port was built at the Config only this project declares.
template<typename Config>
void xpSktChk<Config>::check(void)
{
    Q_ASSERT(SK_PIXEL_WIDTH == ASM_WIDTH,
        std::format("xpSktChk must resolve SK_PIXEL_WIDTH to {} but resolved {}",
            ASM_WIDTH, (uint64_t)SK_PIXEL_WIDTH));
    m_eot.registerVoter();
    skSampleSt sample{};
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        in->pushReceive(sample);
        in->ack();
        log_.logPrint(std::format("{} received tag {} data 0x{:x}", this->name(),
            (uint64_t)sample.tag, (uint64_t)sample.data), LOG_IMPORTANT);
        Q_ASSERT((uint64_t)sample.tag == i, "xpSktChk tag field mismatch");
        Q_ASSERT((uint64_t)sample.data == FIRST_PIXEL + i, "xpSktChk data field mismatch");
    }
    log_.logPrint(std::format("{} checked {} samples at pixel width {}", this->name(),
        SAMPLE_COUNT, (uint64_t)SK_PIXEL_WIDTH), LOG_IMPORTANT);
    m_eot.setEndOfTest(true);
}

