//

// GENERATED_CODE_PARAM --block=bvhFifo --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "rdy_vld_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module bfmVlHandover_bvhFifo.block;
import bfmVlHandover_bvhFifo.base;
import bfmVlHandover_bvh;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace bfmVlHandover_bvh_ns;
export SC_MODULE(bvhFifo), public blockBase, public bvhFifoBase
{
private:

public:

    bvhFifo(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~bvhFifo() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    void forward(void);

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(bvhFifo);

// === Block factory registration (bvhFifo) ===
void register_bvhFifo_variants() {
    instanceFactory::registerBlock("bvhFifo_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<bvhFifo>(blockName, variant, bbMode)); }, "", "bfmVlHandover");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _bvhFifo_registered = (register_bvhFifo_variants(), 0);
} // namespace
// === End block factory registration ===

bvhFifo::bvhFifo(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("bvhFifo", name(), bbMode)
        ,bvhFifoBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(forward);
};

// Stands in for the RTL in a model-only run.
void bvhFifo::forward(void)
{
    bvhBeat beat;
    while (true) {
        in->read(beat);
        out->write(beat);
    }
}
