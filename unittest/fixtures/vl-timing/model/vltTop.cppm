//

// GENERATED_CODE_PARAM --block=vltTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module vlTiming_vltTop.block;
import vlTiming_vltTop.base;
import vlTiming_vlt;
import vlTiming_vltSrc.base;
import vlTiming_vltChk.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace vlTiming_vlt_ns;
export SC_MODULE(vltTop), public blockBase, public vltTopBase
{
private:

public:
    // channels
    // Single-sample push/ack stream
    push_ack_channel< vltSt > out;

    //instances contained in block
    std::shared_ptr<vltSrcBase> uSrc;
    std::shared_ptr<vltChkBase> uChk;

    vltTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~vltTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(vltTop);

// === Block factory registration (vltTop) ===
void register_vltTop_variants() {
    instanceFactory::registerBlock("vltTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vltTop>(blockName, variant, bbMode)); }, "", "vlTiming");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _vltTop_registered = (register_vltTop_variants(), 0);
} // namespace
// === End block factory registration ===

vltTop::vltTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("vltTop", name(), bbMode)
        ,vltTopBase(name(), variant)
        ,out("vltChk_out", "vltSrc")
        ,uSrc(std::dynamic_pointer_cast<vltSrcBase>(instanceFactory::createInstance(name(), "uSrc", "vltSrc", "", "vlTiming")))
        ,uChk(std::dynamic_pointer_cast<vltChkBase>(instanceFactory::createInstance(name(), "uChk", "vltChk", "", "vlTiming")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uSrc->out(out);
    uChk->in(out);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
