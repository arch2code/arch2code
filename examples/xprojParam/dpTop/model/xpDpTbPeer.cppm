//

// GENERATED_CODE_PARAM --block=xpDpTbPeer --mode=module
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
export module xpDpTop_xpDpTbPeer.block;
import xpDpTop_xpDpTbPeer.base;
import xpDpTop.xpDpTbPeer.config;
import xpDpLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpDpLeaf_ns;
export template<typename Config>
SC_MODULE(xpDpTbPeer), public blockBase, public xpDpTbPeerBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpDpTbPeer);

    // inherited names usable unqualified (no Config:: / this->)
    using xpDpTbPeerBase<Config>::DP_ALGO;
    using xpDpTbPeerBase<Config>::DP_WIDTH;
    using xpDpTbPeerBase<Config>::out;
    using xpDpTbPeerBase<Config>::in;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpDpTbPeerBase<Config>::dpPixelT;
    using typename xpDpTbPeerBase<Config>::dpSt;

    xpDpTbPeer(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpDpTbPeer() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // The algorithm this peer resolved from its OWN Config. Both peers are
    // configured to the same number by different routes - one variant states it
    // directly, the other sources it from the testbench container - so each
    // peer stamping its own value and asserting the value it receives compares
    // the two routes against each other.
    static constexpr uint32_t PEER_ALGO = Config::DP_ALGO;
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_TAG = 0;
    static constexpr uint32_t FIRST_DATA = 0x31;
    static constexpr uint32_t FIRST_MARK = 0x50;
    void drive(void);
    void check(void);
    endOfTest m_eot;

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpDpTbPeer<Config>::xpDpTbPeer(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpDpTbPeer", name(), bbMode)
        ,xpDpTbPeerBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(drive);
    SC_THREAD(check);
};

// Drives four samples stamped with the algorithm this peer resolved. Driving and
// checking are separate threads so the two peers feeding each other cannot
// deadlock on the blocking push.
template<typename Config>
void xpDpTbPeer<Config>::drive(void)
{
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        dpSt sample{};
        sample.tag  = FIRST_TAG + i;
        sample.algo = PEER_ALGO;
        sample.data = FIRST_DATA + i;
        sample.mark = FIRST_MARK + i;
        out->push(sample);
    }
}

// Checks every field, and in particular that the algorithm the sending peer
// stamped matches the one this peer resolved.
template<typename Config>
void xpDpTbPeer<Config>::check(void)
{
    m_eot.registerVoter();
    dpSt sample{};
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        in->pushReceive(sample);
        in->ack();
        Q_ASSERT((uint64_t)sample.tag  == FIRST_TAG + i,  "xpDpTbPeer tag field mismatch");
        Q_ASSERT((uint64_t)sample.data == FIRST_DATA + i, "xpDpTbPeer data field mismatch");
        Q_ASSERT((uint64_t)sample.mark == FIRST_MARK + i, "xpDpTbPeer mark field mismatch");
        Q_ASSERT((uint64_t)sample.algo == PEER_ALGO,
            std::format("this peer resolved algorithm {} but its partner stamped {}",
                PEER_ALGO, (uint64_t)sample.algo));
    }
    log_.logPrint(std::format("{} checked {} samples at algorithm {}", this->name(),
        SAMPLE_COUNT, (uint64_t)PEER_ALGO), LOG_IMPORTANT);
    m_eot.setEndOfTest(true);
}

