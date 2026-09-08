//

// GENERATED_CODE_PARAM --block=xpCppLeafEq --mode=module
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
export module xpCppLeaf_xpCppLeafEq.block;
import xpCppLeaf_xpCppLeafEq.base;
import xpCppLeaf.xpCppLeafEq.config;
import xpCppLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpCppLeaf_ns;
export template<typename Config>
SC_MODULE(xpCppLeafEq), public blockBase, public xpCppLeafEqBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpCppLeafEq);

    // inherited names usable unqualified (no Config:: / this->)
    using xpCppLeafEqBase<Config>::LEAF_PIXEL_WIDTH;
    using xpCppLeafEqBase<Config>::eqIn;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpCppLeafEqBase<Config>::leafPixelT;
    using typename xpCppLeafEqBase<Config>::leafSignedPixelT;
    using typename xpCppLeafEqBase<Config>::leafEqSt;
    using typename xpCppLeafEqBase<Config>::leafOrderSt;
    using typename xpCppLeafEqBase<Config>::leafSignSt;
    using typename xpCppLeafEqBase<Config>::leafNestSt;

    xpCppLeafEq(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpCppLeafEq() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // Sample count and first pixel the driver produces on this shape.
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_PIXEL = 0x10;
    void checkEq(void);
    endOfTest m_eot;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpCppLeafEq<Config>::xpCppLeafEq(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpCppLeafEq", name(), bbMode)
        ,xpCppLeafEqBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(checkEq);
};

// Checks every field of every sample. This junction's two declarations carry
// identical member storage, so it is the pair a direct payload copy could serve.
template<typename Config>
void xpCppLeafEq<Config>::checkEq(void)
{
    Q_ASSERT(LEAF_PIXEL_WIDTH == 8, "xpCppLeafEq LEAF_PIXEL_WIDTH must resolve to the bound variant value 8");
    m_eot.registerVoter();
    leafEqSt sample;
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        eqIn->pushReceive(sample);
        eqIn->ack();
        log_.logPrint(std::format("{} received tag {} pixel 0x{:x}", this->name(),
            (uint64_t)sample.tag, (uint64_t)sample.data), LOG_IMPORTANT);
        Q_ASSERT((uint64_t)sample.tag == i, "eq shape delivered samples out of order");
        Q_ASSERT((uint64_t)sample.data == FIRST_PIXEL + i, "eq shape delivered an unexpected pixel");
    }
    log_.logPrint(std::format("{} checked {} samples", this->name(), SAMPLE_COUNT), LOG_IMPORTANT);
    m_eot.setEndOfTest(true);
}

