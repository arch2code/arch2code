//

// GENERATED_CODE_PARAM --block=xpCppLeafNest --mode=module
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
export module xpCppLeaf_xpCppLeafNest.block;
import xpCppLeaf_xpCppLeafNest.base;
import xpCppLeaf.xpCppLeafNest.config;
import xpCppLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpCppLeaf_ns;
export template<typename Config>
SC_MODULE(xpCppLeafNest), public blockBase, public xpCppLeafNestBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpCppLeafNest);

    // inherited names usable unqualified (no Config:: / this->)
    using xpCppLeafNestBase<Config>::LEAF_PIXEL_WIDTH;
    using xpCppLeafNestBase<Config>::nestIn;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpCppLeafNestBase<Config>::leafPixelT;
    using typename xpCppLeafNestBase<Config>::leafSignedPixelT;
    using typename xpCppLeafNestBase<Config>::leafEqSt;
    using typename xpCppLeafNestBase<Config>::leafOrderSt;
    using typename xpCppLeafNestBase<Config>::leafSignSt;
    using typename xpCppLeafNestBase<Config>::leafNestSt;

    xpCppLeafNest(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpCppLeafNest() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // Sample count and first value per field the driver produces on this shape.
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t WORD_BASE = 0x11110000;
    static constexpr uint32_t FIRST_FLAG = 0x40;
    static constexpr uint32_t FIRST_TAIL = 0x50;
    static constexpr uint32_t FIRST_PIXEL = 0x60;
    void checkNest(void);
    endOfTest m_eot;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpCppLeafNest<Config>::xpCppLeafNest(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpCppLeafNest", name(), bbMode)
        ,xpCppLeafNestBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(checkNest);
};

// Checks every field of every sample. This junction pairs a nested declaration
// against a flat one at the same bit positions: the packed sequences match while
// the member sequences and the emitted sizeof do not.
template<typename Config>
void xpCppLeafNest<Config>::checkNest(void)
{
    Q_ASSERT(LEAF_PIXEL_WIDTH == 8, "xpCppLeafNest LEAF_PIXEL_WIDTH must resolve to the bound variant value 8");
    m_eot.registerVoter();
    leafNestSt sample;
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        nestIn->pushReceive(sample);
        nestIn->ack();
        log_.logPrint(std::format("{} received word 0x{:x} flag 0x{:x} tail 0x{:x} pixel 0x{:x}",
            this->name(), (uint64_t)sample.word, (uint64_t)sample.flag,
            (uint64_t)sample.tail, (uint64_t)sample.data), LOG_IMPORTANT);
        Q_ASSERT((uint64_t)sample.word == WORD_BASE + i, "nest shape delivered an unexpected header word");
        Q_ASSERT((uint64_t)sample.flag == FIRST_FLAG + i, "nest shape delivered an unexpected header flag");
        Q_ASSERT((uint64_t)sample.tail == FIRST_TAIL + i, "nest shape delivered an unexpected trailing flag");
        Q_ASSERT((uint64_t)sample.data == FIRST_PIXEL + i, "nest shape delivered an unexpected pixel");
    }
    log_.logPrint(std::format("{} checked {} samples", this->name(), SAMPLE_COUNT), LOG_IMPORTANT);
    m_eot.setEndOfTest(true);
}

