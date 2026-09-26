//

// GENERATED_CODE_PARAM --block=xpDpMidStdWrap --mode=module
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
export module xpDpMid_xpDpMidStdWrap.block;
import xpDpMid_xpDpMidStdWrap.base;
import xpDpMid.config;
import xpDpMid.xpDpMidDrv.config;
import xpDpMid.xpDpMidSnk.config;
import xpDpLeaf;
import xpDpMid_xpDpMidDrv.base;
import xpDpMid.base;
import xpDpMid_xpDpMidSnk.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpDpLeaf_ns;
export SC_MODULE(xpDpMidStdWrap), public blockBase, public xpDpMidStdWrapBase
{
private:

public:
    // channels
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<xpDpMidStdConfig> > out;
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<xpDpMid_xpDpMidSnkStdConfig> > midOut;

    //instances contained in block
    std::shared_ptr<xpDpMidDrvBase<xpDpMid_xpDpMidDrvStdConfig>> uDrv;
    std::shared_ptr<xpDpMidBase<xpDpMidStdConfig>> uMidStd;
    std::shared_ptr<xpDpMidSnkBase<xpDpMid_xpDpMidSnkStdConfig>> uSnk;

    xpDpMidStdWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpDpMidStdWrap() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpDpMidStdWrap);

// === Block factory registration (xpDpMidStdWrap) ===
void register_xpDpMidStdWrap_variants() {
    instanceFactory::registerBlock("xpDpMidStdWrap_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpMidStdWrap>(blockName, variant, bbMode)); }, "", "xpDpMid");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpDpMidStdWrap_registered = (register_xpDpMidStdWrap_variants(), 0);
} // namespace
// === End block factory registration ===

xpDpMidStdWrap::xpDpMidStdWrap(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpDpMidStdWrap", name(), bbMode)
        ,xpDpMidStdWrapBase(name(), variant)
        ,out("xpDpMid_out", "xpDpMidDrv")
        ,midOut("xpDpMidSnk_midOut", "xpDpMid")
        ,uDrv(std::dynamic_pointer_cast<xpDpMidDrvBase<xpDpMid_xpDpMidDrvStdConfig>>(instanceFactory::createInstance(name(), "uDrv", "xpDpMidDrv", "std", "xpDpMid.xpDpMid_xpDpMidStdWrap.xpDpMid_xpDpMidDrv")))
        ,uMidStd(std::dynamic_pointer_cast<xpDpMidBase<xpDpMidStdConfig>>(instanceFactory::createInstance(name(), "uMidStd", "xpDpMid", "std", "xpDpMid.xpDpMid_xpDpMidStdWrap.xpDpMid")))
        ,uSnk(std::dynamic_pointer_cast<xpDpMidSnkBase<xpDpMid_xpDpMidSnkStdConfig>>(instanceFactory::createInstance(name(), "uSnk", "xpDpMidSnk", "std", "xpDpMid.xpDpMid_xpDpMidStdWrap.xpDpMid_xpDpMidSnk")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uDrv->out(out);
    uMidStd->midIn(out);
    uMidStd->midOut(midOut);
    uSnk->in(midOut);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

