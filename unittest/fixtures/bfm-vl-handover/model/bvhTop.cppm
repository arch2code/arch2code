//

// GENERATED_CODE_PARAM --block=bvhTop --mode=module
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
export module bfmVlHandover_bvhTop.block;
import bfmVlHandover_bvhTop.base;
import bfmVlHandover_bvh;
import bfmVlHandover_bvhSrc.base;
import bfmVlHandover_bvhFifo.base;
import bfmVlHandover_bvhSnk.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace bfmVlHandover_bvh_ns;
export SC_MODULE(bvhTop), public blockBase, public bvhTopBase
{
private:

public:
    // channels
    // Beat stream
    rdy_vld_channel< bvhBeat > out_0;
    // Beat stream
    rdy_vld_channel< bvhBeat > out_1;

    //instances contained in block
    std::shared_ptr<bvhSrcBase> uSrc;
    std::shared_ptr<bvhFifoBase> uFifo;
    std::shared_ptr<bvhSnkBase> uSnk;

    bvhTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~bvhTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(bvhTop);

// === Block factory registration (bvhTop) ===
void register_bvhTop_variants() {
    instanceFactory::registerBlock("bvhTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<bvhTop>(blockName, variant, bbMode)); }, "", "bfmVlHandover");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _bvhTop_registered = (register_bvhTop_variants(), 0);
} // namespace
// === End block factory registration ===

bvhTop::bvhTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("bvhTop", name(), bbMode)
        ,bvhTopBase(name(), variant)
        ,out_0("bvhFifo_out_0", "bvhSrc", BACKPRESSURE_ALLOWED)
        ,out_1("bvhSnk_out_1", "bvhFifo", BACKPRESSURE_ALLOWED)
        ,uSrc(std::dynamic_pointer_cast<bvhSrcBase>(instanceFactory::createInstance(name(), "uSrc", "bvhSrc", "", "bfmVlHandover")))
        ,uFifo(std::dynamic_pointer_cast<bvhFifoBase>(instanceFactory::createInstance(name(), "uFifo", "bvhFifo", "", "bfmVlHandover")))
        ,uSnk(std::dynamic_pointer_cast<bvhSnkBase>(instanceFactory::createInstance(name(), "uSnk", "bvhSnk", "", "bfmVlHandover")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uSrc->out(out_0);
    uFifo->in(out_0);
    uFifo->out(out_1);
    uSnk->in(out_1);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
