//

// GENERATED_CODE_PARAM --block=xpSktAsmTop --mode=module
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
export module xpSktAsm_xpSktAsmTop.block;
import xpSktAsm_xpSktAsmTop.base;
import xpSktAsm.xpSktChk.config;
import xpSktAsm.xpSktLeaf.config;
import xpSktIp;
import xpSktIp_xpSktLeaf.base;
import xpSktAsm_xpSktChk.base;
import xpSktAsm_xpSktAsmTop;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpSktIp_ns;
using namespace xpSktAsm_xpSktAsmTop_ns;
export SC_MODULE(xpSktAsmTop), public blockBase, public xpSktAsmTopBase
{
private:

public:
    // channels
    // The IP's parameterized sample push/ack stream
    push_ack_channel< skSampleSt<xpSktAsm_xpSktChkAsmConfig> > out;

    //instances contained in block
    std::shared_ptr<xpSktLeafBase<xpSktAsm_xpSktLeafAsmConfig>> uLeaf;
    std::shared_ptr<xpSktChkBase<xpSktAsm_xpSktChkAsmConfig>> uChk;

    xpSktAsmTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpSktAsmTop() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // The testbench config creates this top directly, with no testbench
    // External in the hierarchy, so the top stops the kernel itself.
    void eotStopSim(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpSktAsmTop);

// === Block factory registration (xpSktAsmTop) ===
void register_xpSktAsmTop_variants() {
    instanceFactory::registerBlock("xpSktAsmTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpSktAsmTop>(blockName, variant, bbMode)); }, "", "xpSktAsm");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpSktAsmTop_registered = (register_xpSktAsmTop_variants(), 0);
} // namespace
// === End block factory registration ===

xpSktAsmTop::xpSktAsmTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpSktAsmTop", name(), bbMode)
        ,xpSktAsmTopBase(name(), variant)
        ,out("xpSktChk_out", "xpSktLeaf")
        ,uLeaf(std::dynamic_pointer_cast<xpSktLeafBase<xpSktAsm_xpSktLeafAsmConfig>>(instanceFactory::createInstance(name(), "uLeaf", "xpSktLeaf", "asm", "xpSktAsm.xpSktAsm_xpSktAsmTop.xpSktIp_xpSktLeaf")))
        ,uChk(std::dynamic_pointer_cast<xpSktChkBase<xpSktAsm_xpSktChkAsmConfig>>(instanceFactory::createInstance(name(), "uChk", "xpSktChk", "asm", "xpSktAsm.xpSktAsm_xpSktAsmTop.xpSktAsm_xpSktChk")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uLeaf->out(out);
    uChk->in(out);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(eotStopSim);
};

void xpSktAsmTop::eotStopSim(void)
{
    endOfTestState &eot = endOfTestState::GetInstance();
    while (!eot.isEndOfTest()) {
        wait(eot.eotEvent);
    }
    sc_stop();
}

