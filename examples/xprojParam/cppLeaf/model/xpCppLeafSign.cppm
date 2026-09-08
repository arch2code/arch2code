//

// GENERATED_CODE_PARAM --block=xpCppLeafSign --mode=module
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
export module xpCppLeaf_xpCppLeafSign.block;
import xpCppLeaf_xpCppLeafSign.base;
import xpCppLeaf.xpCppLeafSign.config;
import xpCppLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpCppLeaf_ns;
export template<typename Config>
SC_MODULE(xpCppLeafSign), public blockBase, public xpCppLeafSignBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpCppLeafSign);

    // inherited names usable unqualified (no Config:: / this->)
    using xpCppLeafSignBase<Config>::LEAF_PIXEL_WIDTH;
    using xpCppLeafSignBase<Config>::signIn;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpCppLeafSignBase<Config>::leafPixelT;
    using typename xpCppLeafSignBase<Config>::leafSignedPixelT;
    using typename xpCppLeafSignBase<Config>::leafEqSt;
    using typename xpCppLeafSignBase<Config>::leafOrderSt;
    using typename xpCppLeafSignBase<Config>::leafSignSt;
    using typename xpCppLeafSignBase<Config>::leafNestSt;

    xpCppLeafSign(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpCppLeafSign() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // Sample count and first pixel the driver produces on this shape.
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_PIXEL = 0x30;
    void checkSign(void);
    endOfTest m_eot;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpCppLeafSign<Config>::xpCppLeafSign(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpCppLeafSign", name(), bbMode)
        ,xpCppLeafSignBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(checkSign);
};

// Checks every sample. This junction's two declarations agree on width and
// position and differ only in signedness, so the pack/unpack adapter and a
// direct copy would produce the same bytes here; the sides are still not
// declaration-identical.
template<typename Config>
void xpCppLeafSign<Config>::checkSign(void)
{
    Q_ASSERT(LEAF_PIXEL_WIDTH == 8, "xpCppLeafSign LEAF_PIXEL_WIDTH must resolve to the bound variant value 8");
    m_eot.registerVoter();
    leafSignSt sample;
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        signIn->pushReceive(sample);
        signIn->ack();
        log_.logPrint(std::format("{} received pixel 0x{:x}", this->name(),
            (int64_t)sample.data), LOG_IMPORTANT);
        Q_ASSERT((int64_t)sample.data == (int64_t)(FIRST_PIXEL + i), "sign shape delivered an unexpected pixel");
    }
    log_.logPrint(std::format("{} checked {} samples", this->name(), SAMPLE_COUNT), LOG_IMPORTANT);
    m_eot.setEndOfTest(true);
}

