//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmVideo --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=testBenchModuleHeader
module;
#include "systemc.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=testBench
export module uvmVideo.testbench;
import uvmVideo.base;
import uvmVideo.external;
import uvmVideo;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=testbench --section=header

using namespace uvmVideo_ns;

export class uvmVideoTestbench: public sc_module, public blockBase, public uvmVideoChannels {

public:

    std::shared_ptr<uvmVideoBase> uvmVideo;
    uvmVideoExternal external;

    uvmVideoTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmVideoTestbench() override = default;

    void setTimed(int nsec, timedDelayMode mode) override
    {
    };

    void setLogging(verbosity_e verbosity) override
    {
    };

};
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=testbench --section=init
// === Block factory registration (uvmVideoTestbench) ===
// The testbench top self-registers through an A2C_REGISTRATION_RETAIN static
// (see instanceFactory.h); main() reaches it through direct-.o linking with no
// force-link reference.
void register_uvmVideoTestbench_variants() {
    instanceFactory::registerBlock("uvmVideoTestbench_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmVideoTestbench>(blockName, variant, bbMode)); }, "", "uvmVideo");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmVideoTestbench_registered = (register_uvmVideoTestbench_variants(), 0);
} // namespace
// === End block factory registration ===

uvmVideoTestbench::uvmVideoTestbench(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : blockBase("uvmVideoTestbench", name(), bbMode)
        ,uvmVideoChannels("Chnl", "tb")
        ,uvmVideo(std::dynamic_pointer_cast<uvmVideoBase>( instanceFactory::createInstance(name(), "uvmVideo", "uvmVideo", "", "uvmVideo")))
        ,external("external")
{
    bind(uvmVideo.get(), &external);
}
// GENERATED_CODE_END
