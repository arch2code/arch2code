//

// GENERATED_CODE_PARAM --block=rdvLeaf --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "rdvTopVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "q_assert.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module rdvTest_rdvLeaf.block;
import rdvTest_rdvLeaf.base;
import rdvTest_rdvTop;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace rdvTest_rdvTop_ns;
export template<typename Config>
SC_MODULE(rdvLeaf), public blockBase, public rdvLeafBase<Config>
{
private:

public:
    SC_HAS_PROCESS(rdvLeaf);

    // inherited names usable unqualified (no Config:: / this->)
    using rdvLeafBase<Config>::RDV_ALGO;
    using rdvLeafBase<Config>::in;


    rdvLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~rdvLeaf() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_DATA = 0x31;
    void check(void);
    endOfTest m_eot;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
rdvLeaf<Config>::rdvLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("rdvLeaf", name(), bbMode)
        ,rdvLeafBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(check);
};

// Reports the algorithm this site resolved and checks the samples it receives.
// Both sites are this one class template at different Configs, so the reported
// algorithm is what tells them apart.
template<typename Config>
void rdvLeaf<Config>::check(void)
{
    m_eot.registerVoter();
    log_.logPrint(std::format("{} resolved algorithm {}", this->name(),
        (uint64_t)RDV_ALGO), LOG_IMPORTANT);
    rdvSt sample{};
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        in->pushReceive(sample);
        in->ack();
        Q_ASSERT((uint64_t)sample.data == FIRST_DATA + i, "rdvLeaf data field mismatch");
    }
    m_eot.setEndOfTest(true);
}

