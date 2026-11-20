//

// GENERATED_CODE_PARAM --block=bvhSnk --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "rdy_vld_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include <cstdlib>
#include <iostream>
#include <string>
#include "q_assert.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module bfmVlHandover_bvhSnk.block;
import bfmVlHandover_bvhSnk.base;
import bfmVlHandover_bvh;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
import a2c.endOfTest;
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace bfmVlHandover_bvh_ns;
export SC_MODULE(bvhSnk), public blockBase, public bvhSnkBase
{
private:

public:

    bvhSnk(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~bvhSnk() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    void receive(void);
    endOfTest m_eot;

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(bvhSnk);

// === Block factory registration (bvhSnk) ===
void register_bvhSnk_variants() {
    instanceFactory::registerBlock("bvhSnk_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<bvhSnk>(blockName, variant, bbMode)); }, "", "bfmVlHandover");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _bvhSnk_registered = (register_bvhSnk_variants(), 0);
} // namespace
// === End block factory registration ===

bvhSnk::bvhSnk(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("bvhSnk", name(), bbMode)
        ,bvhSnkBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(receive);
};

// BVH_MODE picks the run, see test_bfm_vl_handover.py. hold starts reading at
// 502 ns and pause stops for 52 ns before beat 8. Both land 2 ns after a clock
// edge, so no read lands on one. BVH_ON_EDGE moves both 2 ns earlier, onto an
// edge.
void bvhSnk::receive(void)
{
    m_eot.registerVoter();
    const char * env = std::getenv("BVH_MODE");
    Q_ASSERT(env != nullptr, "BVH_MODE is not set");
    if (env == nullptr) {
        return;
    }
    const std::string mode = env;
    const bool known = mode == "single" || mode == "burst" || mode == "hold" || mode == "pause" || mode == "poweron";
    Q_ASSERT(known, "unknown BVH_MODE " + mode);
    if (!known) {
        return;
    }
    const unsigned beats = (mode == "single" || mode == "poweron") ? 1 : 16;
    const sc_time shift = std::getenv("BVH_ON_EDGE") ? sc_time(2, SC_NS) : SC_ZERO_TIME;
    if (mode == "hold") {
        wait(sc_time(502, SC_NS) - shift);
    }
    for (unsigned k = 0; k < beats; k++) {
        bvhBeat beat;
        if (mode == "pause" && k == 8) {
            wait(sc_time(52, SC_NS) - shift);
        }
        std::cout << "BVH snk call " << k << " " << sc_time_stamp().value() << std::endl;
        in->read(beat);
        std::cout << "BVH snk recv " << k << " " << (unsigned)beat.data << " " << sc_time_stamp().value() << std::endl;
    }
    // A few more edges, so the trace holds the last handshake.
    wait(sc_time(50, SC_NS));
    m_eot.setEndOfTest(true);
}
