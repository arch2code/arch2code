//

// GENERATED_CODE_PARAM --block=xviTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "push_ack_port_thunker.h"
#include "xviLeafVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xviTop.block;
import xviTop.base;
import xviTop.xviLeaf.config;
import xviTop.xviTopDrv.config;
import xviTop.xviTopSnk.config;
import xviLeaf;
import xviTop_xviTopDrv.base;
import xviLeaf.base;
import xviTop_xviTopSnk.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xviLeaf_ns;
export SC_MODULE(xviTop), public blockBase, public xviTopBase
{
private:

public:
    // channels
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< xviSt<xviTop_xviLeafV0Config> > out_0;
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< xviSt<xviTop_xviTopSnkV0Config> > out_1;
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< xviSt<xviTop_xviLeafVTopConfig> > out_2;
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< xviSt<xviTop_xviTopSnkV0Config> > out_3;

    //instances contained in block
    std::shared_ptr<xviTopDrvBase<xviTop_xviTopDrvV0Config>> uTopDrv;
    std::shared_ptr<xviLeafBase<xviTop_xviLeafV0Config>> uTopLeaf;
    std::shared_ptr<xviTopSnkBase<xviTop_xviTopSnkV0Config>> uTopSnk;
    std::shared_ptr<xviTopDrvBase<xviTop_xviTopDrvV0Config>> uTopOwnDrv;
    std::shared_ptr<xviLeafBase<xviTop_xviLeafVTopConfig>> uTopOwnLeaf;
    std::shared_ptr<xviTopSnkBase<xviTop_xviTopSnkV0Config>> uTopOwnSnk;

    // cross-interface thunkers
    push_ack_port_thunker<xviSt<xviTop_xviLeafV0Config>, xviSt<xviTop_xviTopDrvV0Config>, true> thunker_out_0_uTopDrv;
    push_ack_port_thunker<xviSt<xviTop_xviTopSnkV0Config>, xviSt<xviTop_xviLeafV0Config>, true> thunker_out_1_uTopLeaf;
    push_ack_port_thunker<xviSt<xviTop_xviLeafVTopConfig>, xviSt<xviTop_xviTopDrvV0Config>, true> thunker_out_2_uTopOwnDrv;
    push_ack_port_thunker<xviSt<xviTop_xviTopSnkV0Config>, xviSt<xviTop_xviLeafVTopConfig>, true> thunker_out_3_uTopOwnLeaf;

    xviTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xviTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xviTop);

// === Block factory registration (xviTop) ===
void register_xviTop_variants() {
    instanceFactory::registerBlock("xviTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviTop>(blockName, variant, bbMode)); }, "", "xviTop");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xviTop_registered = (register_xviTop_variants(), 0);
} // namespace
// === End block factory registration ===

xviTop::xviTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xviTop", name(), bbMode)
        ,xviTopBase(name(), variant)
        ,out_0("xviLeaf_out_0", "xviTopDrv")
        ,out_1("xviTopSnk_out_1", "xviLeaf")
        ,out_2("xviLeaf_out_2", "xviTopDrv")
        ,out_3("xviTopSnk_out_3", "xviLeaf")
        ,uTopDrv(std::dynamic_pointer_cast<xviTopDrvBase<xviTop_xviTopDrvV0Config>>(instanceFactory::createInstance(name(), "uTopDrv", "xviTopDrv", "v0", "xviTop.xviTop.xviTop_xviTopDrv")))
        ,uTopLeaf(std::dynamic_pointer_cast<xviLeafBase<xviTop_xviLeafV0Config>>(instanceFactory::createInstance(name(), "uTopLeaf", "xviLeaf", "v0", "xviTop.xviTop.xviLeaf")))
        ,uTopSnk(std::dynamic_pointer_cast<xviTopSnkBase<xviTop_xviTopSnkV0Config>>(instanceFactory::createInstance(name(), "uTopSnk", "xviTopSnk", "v0", "xviTop.xviTop.xviTop_xviTopSnk")))
        ,uTopOwnDrv(std::dynamic_pointer_cast<xviTopDrvBase<xviTop_xviTopDrvV0Config>>(instanceFactory::createInstance(name(), "uTopOwnDrv", "xviTopDrv", "v0", "xviTop.xviTop.xviTop_xviTopDrv")))
        ,uTopOwnLeaf(std::dynamic_pointer_cast<xviLeafBase<xviTop_xviLeafVTopConfig>>(instanceFactory::createInstance(name(), "uTopOwnLeaf", "xviLeaf", "vTop", "xviTop.xviTop.xviLeaf")))
        ,uTopOwnSnk(std::dynamic_pointer_cast<xviTopSnkBase<xviTop_xviTopSnkV0Config>>(instanceFactory::createInstance(name(), "uTopOwnSnk", "xviTopSnk", "v0", "xviTop.xviTop.xviTop_xviTopSnk")))
        ,thunker_out_0_uTopDrv("thunker_out_0_uTopDrv", out_0, uTopDrv->out, name())
        ,thunker_out_1_uTopLeaf("thunker_out_1_uTopLeaf", out_1, uTopLeaf->out, name())
        ,thunker_out_2_uTopOwnDrv("thunker_out_2_uTopOwnDrv", out_2, uTopOwnDrv->out, name())
        ,thunker_out_3_uTopOwnLeaf("thunker_out_3_uTopOwnLeaf", out_3, uTopOwnLeaf->out, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uTopLeaf->in(out_0);
    uTopSnk->in(out_1);
    uTopOwnLeaf->in(out_2);
    uTopOwnSnk->in(out_3);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

