//

// GENERATED_CODE_PARAM --block=vltChk --mode=module
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
export module vlTiming_vltChk.block;
import vlTiming_vltChk.base;
import vlTiming_vlt;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace vlTiming_vlt_ns;
export SC_MODULE(vltChk), public blockBase, public vltChkBase
{
private:

public:

    vltChk(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~vltChk() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    static constexpr vltStampT EXPECTED_STAMP_PS = VLT_START_DELAY_PS;
    void check(void);
    endOfTest m_eot;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(vltChk);

// === Block factory registration (vltChk) ===
void register_vltChk_variants() {
    instanceFactory::registerBlock("vltChk_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vltChk>(blockName, variant, bbMode)); }, "", "vlTiming");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _vltChk_registered = (register_vltChk_variants(), 0);
} // namespace
// === End block factory registration ===

vltChk::vltChk(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("vltChk", name(), bbMode)
        ,vltChkBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(check);
};

// The stamp is the time the source's start-up delay ended. A source that never
// waited on the delay stamps 0.
void vltChk::check(void)
{
    m_eot.registerVoter();
    vltSt sample{};
    in->pushReceive(sample);
    in->ack();
    log_.logPrint(std::format("{} received stamp {}", this->name(), (uint64_t)sample.stamp), LOG_IMPORTANT);
    Q_ASSERT((uint64_t)sample.stamp == EXPECTED_STAMP_PS,
        std::format("source stamped {}ps, expected its delay to end at {}ps",
            (uint64_t)sample.stamp, EXPECTED_STAMP_PS));
    m_eot.setEndOfTest(true);
}
