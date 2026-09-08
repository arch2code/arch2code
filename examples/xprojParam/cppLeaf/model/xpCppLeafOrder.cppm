//

// GENERATED_CODE_PARAM --block=xpCppLeafOrder --mode=module
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
export module xpCppLeaf_xpCppLeafOrder.block;
import xpCppLeaf_xpCppLeafOrder.base;
import xpCppLeaf.xpCppLeafOrder.config;
import xpCppLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpCppLeaf_ns;
export template<typename Config>
SC_MODULE(xpCppLeafOrder), public blockBase, public xpCppLeafOrderBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpCppLeafOrder);

    // inherited names usable unqualified (no Config:: / this->)
    using xpCppLeafOrderBase<Config>::LEAF_PIXEL_WIDTH;
    using xpCppLeafOrderBase<Config>::orderIn;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpCppLeafOrderBase<Config>::leafPixelT;
    using typename xpCppLeafOrderBase<Config>::leafSignedPixelT;
    using typename xpCppLeafOrderBase<Config>::leafEqSt;
    using typename xpCppLeafOrderBase<Config>::leafOrderSt;
    using typename xpCppLeafOrderBase<Config>::leafSignSt;
    using typename xpCppLeafOrderBase<Config>::leafNestSt;

    xpCppLeafOrder(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpCppLeafOrder() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // Sample count and first value the driver produces in each packed position.
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_FIRST = 0x20;
    static constexpr uint32_t FIRST_SECOND = 0x70;
    void checkOrder(void);
    endOfTest m_eot;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpCppLeafOrder<Config>::xpCppLeafOrder(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpCppLeafOrder", name(), bbMode)
        ,xpCppLeafOrderBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(checkOrder);
};

// Checks every field of every sample. Each field occupies the same packed
// position as its namesake on the wrapper side, so the values arrive intact,
// while the two declarations place their parameterizable member at opposite
// positions and therefore carry reversed member storage sequences.
template<typename Config>
void xpCppLeafOrder<Config>::checkOrder(void)
{
    Q_ASSERT(LEAF_PIXEL_WIDTH == 8, "xpCppLeafOrder LEAF_PIXEL_WIDTH must resolve to the bound variant value 8");
    m_eot.registerVoter();
    leafOrderSt sample;
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        orderIn->pushReceive(sample);
        orderIn->ack();
        log_.logPrint(std::format("{} received first 0x{:x} second 0x{:x}", this->name(),
            (uint64_t)sample.first, (uint64_t)sample.second), LOG_IMPORTANT);
        Q_ASSERT((uint64_t)sample.first == FIRST_FIRST + i, "order shape delivered an unexpected low-position value");
        Q_ASSERT((uint64_t)sample.second == FIRST_SECOND + i, "order shape delivered an unexpected high-position value");
    }
    log_.logPrint(std::format("{} checked {} samples", this->name(), SAMPLE_COUNT), LOG_IMPORTANT);
    m_eot.setEndOfTest(true);
}

