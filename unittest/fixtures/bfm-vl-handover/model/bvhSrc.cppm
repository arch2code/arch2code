//

// GENERATED_CODE_PARAM --block=bvhSrc --mode=module
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
export module bfmVlHandover_bvhSrc.block;
import bfmVlHandover_bvhSrc.base;
import bfmVlHandover_bvh;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
import a2c.endOfTest;
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace bfmVlHandover_bvh_ns;
export SC_MODULE(bvhSrc), public blockBase, public bvhSrcBase
{
private:

public:

    bvhSrc(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~bvhSrc() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    void send(void);
    endOfTest m_eot;

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(bvhSrc);

// === Block factory registration (bvhSrc) ===
void register_bvhSrc_variants() {
    instanceFactory::registerBlock("bvhSrc_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<bvhSrc>(blockName, variant, bbMode)); }, "", "bfmVlHandover");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _bvhSrc_registered = (register_bvhSrc_variants(), 0);
} // namespace
// === End block factory registration ===

bvhSrc::bvhSrc(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("bvhSrc", name(), bbMode)
        ,bvhSrcBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(send);
};

// BVH_MODE picks the run, see test_bfm_vl_handover.py. Every call and return is
// logged with its simulation time in picoseconds. A beat carries its index.
void bvhSrc::send(void)
{
    m_eot.registerVoter();
    const std::string mode = std::getenv("BVH_MODE");
    const unsigned beats = (mode == "single" || mode == "poweron") ? 1 : 16;
    // 103 ns is 3 ns after a clock edge, and 70 ns after reset releases, so the
    // BFM is already waiting for a beat.
    if (mode != "poweron") {
        wait(sc_time(103, SC_NS));
    }
    for (unsigned k = 0; k < beats; k++) {
        bvhBeat beat;
        beat.data = k;
        std::cout << "BVH src call " << k << " " << sc_time_stamp().value() << std::endl;
        out->write(beat);
        std::cout << "BVH src ret " << k << " " << sc_time_stamp().value() << std::endl;
    }
    m_eot.setEndOfTest(true);
}
