//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClk --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "apb_channel.h"
#include "push_ack_channel.h"
// GENERATED_CODE_END
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module twoClk.block;
import twoClk.base;
import twoClk;
import twoClkIp;
import twoClkIp_twoClkIpSrc.base;
import twoClk_twoClkSink.base;
import twoClk_twoClkSlowTick.base;
import twoClk_twoClkSlowSink.base;
import twoClk_twoClkDecode.base;
import twoClk_twoClkTable.base;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace twoClk_ns;
using namespace twoClkIp_ns;
export SC_MODULE(twoClk), public blockBase, public twoClkBase
{
private:

public:
    // channels
    // twoClkIpSrc -> assembler sink data stream
    push_ack_channel< twoClkDataSt > out_0;
    // twoClkIpSrc -> assembler sink data stream
    push_ack_channel< twoClkDataSt > out_1;
    // twoClkCpu access to twoClkTable's tbl memory
    apb_channel< twoClkRegAddrSt, twoClkRegDataSt > twoClkReg_uTable;

    //instances contained in block
    std::shared_ptr<twoClkIpSrcBase> uIpSrc;
    std::shared_ptr<twoClkSinkBase> uSink;
    std::shared_ptr<twoClkSlowTickBase> uSlowTick;
    std::shared_ptr<twoClkSlowSinkBase> uSlowSink;
    std::shared_ptr<twoClkDecodeBase> uDecode;
    std::shared_ptr<twoClkTableBase> uTable;

    twoClk(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~twoClk() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(twoClk);

// === Block factory registration (twoClk) ===
void register_twoClk_variants() {
    instanceFactory::registerBlock("twoClk_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<twoClk>(blockName, variant, bbMode)); }, "", "twoClk");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _twoClk_registered = (register_twoClk_variants(), 0);
} // namespace
// === End block factory registration ===

twoClk::twoClk(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("twoClk", name(), bbMode)
        ,twoClkBase(name(), variant)
        ,out_0("twoClkSink_out_0", "twoClkIpSrc")
        ,out_1("twoClkSlowSink_out_1", "twoClkSlowTick")
        ,twoClkReg_uTable("twoClkTable_twoClkReg_uTable", "twoClkDecode")
        ,uIpSrc(std::dynamic_pointer_cast<twoClkIpSrcBase>(instanceFactory::createInstance(name(), "uIpSrc", "twoClkIpSrc", "", "twoClkIp")))
        ,uSink(std::dynamic_pointer_cast<twoClkSinkBase>(instanceFactory::createInstance(name(), "uSink", "twoClkSink", "", "twoClk")))
        ,uSlowTick(std::dynamic_pointer_cast<twoClkSlowTickBase>(instanceFactory::createInstance(name(), "uSlowTick", "twoClkSlowTick", "", "twoClk")))
        ,uSlowSink(std::dynamic_pointer_cast<twoClkSlowSinkBase>(instanceFactory::createInstance(name(), "uSlowSink", "twoClkSlowSink", "", "twoClk")))
        ,uDecode(std::dynamic_pointer_cast<twoClkDecodeBase>(instanceFactory::createInstance(name(), "uDecode", "twoClkDecode", "", "twoClk")))
        ,uTable(std::dynamic_pointer_cast<twoClkTableBase>(instanceFactory::createInstance(name(), "uTable", "twoClkTable", "", "twoClk")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uDecode->twoClkReg(twoClkReg);
    // instance to instance connections via channel
    uIpSrc->out(out_0);
    uSink->in(out_0);
    uSlowTick->out(out_1);
    uSlowSink->in(out_1);
    uDecode->twoClkReg_uTable(twoClkReg_uTable);
    uTable->twoClkReg(twoClkReg_uTable);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

