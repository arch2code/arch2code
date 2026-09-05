//

// GENERATED_CODE_PARAM --block=xviMid --mode=module
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
export module xviMid.block;
import xviMid.base;
import xviMid.xviDrv.config;
import xviMid.xviLeaf.config;
import xviMid.xviSnk.config;
import xviLeaf;
import xviMid_xviDrv.base;
import xviLeaf.base;
import xviMid_xviSnk.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xviLeaf_ns;
export SC_MODULE(xviMid), public blockBase, public xviMidBase
{
private:

public:
    // channels
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< xviSt<xviMid_xviLeafV0Config> > out_0;
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< xviSt<xviMid_xviSnkV0Config> > out_1;
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< xviSt<xviMid_xviLeafVMidConfig> > out_2;
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< xviSt<xviMid_xviSnkV0Config> > out_3;

    //instances contained in block
    std::shared_ptr<xviDrvBase<xviMid_xviDrvV0Config>> uMidDrv;
    std::shared_ptr<xviLeafBase<xviMid_xviLeafV0Config>> uMidLeaf;
    std::shared_ptr<xviSnkBase<xviMid_xviSnkV0Config>> uMidSnk;
    std::shared_ptr<xviDrvBase<xviMid_xviDrvV0Config>> uMidOwnDrv;
    std::shared_ptr<xviLeafBase<xviMid_xviLeafVMidConfig>> uMidOwnLeaf;
    std::shared_ptr<xviSnkBase<xviMid_xviSnkV0Config>> uMidOwnSnk;

    // cross-interface thunkers
    push_ack_port_thunker<xviSt<xviMid_xviLeafV0Config>, xviSt<xviMid_xviDrvV0Config>, true> thunker_out_0_uMidDrv;
    push_ack_port_thunker<xviSt<xviMid_xviSnkV0Config>, xviSt<xviMid_xviLeafV0Config>, true> thunker_out_1_uMidLeaf;
    push_ack_port_thunker<xviSt<xviMid_xviLeafVMidConfig>, xviSt<xviMid_xviDrvV0Config>, true> thunker_out_2_uMidOwnDrv;
    push_ack_port_thunker<xviSt<xviMid_xviSnkV0Config>, xviSt<xviMid_xviLeafVMidConfig>, true> thunker_out_3_uMidOwnLeaf;

    xviMid(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xviMid() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xviMid);

// === Block factory registration (xviMid) ===
void register_xviMid_variants() {
    instanceFactory::registerBlock("xviMid_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviMid>(blockName, variant, bbMode)); }, "", "xviMid");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xviMid_registered = (register_xviMid_variants(), 0);
} // namespace
// === End block factory registration ===

xviMid::xviMid(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xviMid", name(), bbMode)
        ,xviMidBase(name(), variant)
        ,out_0("xviLeaf_out_0", "xviDrv")
        ,out_1("xviSnk_out_1", "xviLeaf")
        ,out_2("xviLeaf_out_2", "xviDrv")
        ,out_3("xviSnk_out_3", "xviLeaf")
        ,uMidDrv(std::dynamic_pointer_cast<xviDrvBase<xviMid_xviDrvV0Config>>(instanceFactory::createInstance(name(), "uMidDrv", "xviDrv", "v0", "xviMid.xviMid.xviMid_xviDrv")))
        ,uMidLeaf(std::dynamic_pointer_cast<xviLeafBase<xviMid_xviLeafV0Config>>(instanceFactory::createInstance(name(), "uMidLeaf", "xviLeaf", "v0", "xviMid.xviMid.xviLeaf")))
        ,uMidSnk(std::dynamic_pointer_cast<xviSnkBase<xviMid_xviSnkV0Config>>(instanceFactory::createInstance(name(), "uMidSnk", "xviSnk", "v0", "xviMid.xviMid.xviMid_xviSnk")))
        ,uMidOwnDrv(std::dynamic_pointer_cast<xviDrvBase<xviMid_xviDrvV0Config>>(instanceFactory::createInstance(name(), "uMidOwnDrv", "xviDrv", "v0", "xviMid.xviMid.xviMid_xviDrv")))
        ,uMidOwnLeaf(std::dynamic_pointer_cast<xviLeafBase<xviMid_xviLeafVMidConfig>>(instanceFactory::createInstance(name(), "uMidOwnLeaf", "xviLeaf", "vMid", "xviMid.xviMid.xviLeaf")))
        ,uMidOwnSnk(std::dynamic_pointer_cast<xviSnkBase<xviMid_xviSnkV0Config>>(instanceFactory::createInstance(name(), "uMidOwnSnk", "xviSnk", "v0", "xviMid.xviMid.xviMid_xviSnk")))
        ,thunker_out_0_uMidDrv("thunker_out_0_uMidDrv", out_0, uMidDrv->out, name())
        ,thunker_out_1_uMidLeaf("thunker_out_1_uMidLeaf", out_1, uMidLeaf->out, name())
        ,thunker_out_2_uMidOwnDrv("thunker_out_2_uMidOwnDrv", out_2, uMidOwnDrv->out, name())
        ,thunker_out_3_uMidOwnLeaf("thunker_out_3_uMidOwnLeaf", out_3, uMidOwnLeaf->out, name())
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uMidLeaf->in(out_0);
    uMidSnk->in(out_1);
    uMidOwnLeaf->in(out_2);
    uMidOwnSnk->in(out_3);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

