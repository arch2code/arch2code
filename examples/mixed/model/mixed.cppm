//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=mixed --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "apb_channel.h"
#include "notify_ack_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"
#include "mixedVariantConfig.h"
// GENERATED_CODE_END
#include "mixedVariantConfig.h"
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module mixed.block;
import mixed.base;
import mixed;
import mixed_mixedBlockC;
import mixed_blockA.base;
import mixed_apbDecode.base;
import mixed_blockC.base;
import mixed_blockB.base;
import mixed_blockG.base;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace mixed_ns;
using namespace mixed_mixedBlockC_ns;
export SC_MODULE(mixed), public blockBase, public mixedBase
{
private:

public:
    // channels
    // An interface for A
    req_ack_channel< aSt, aASt > aStuffIf;
    // An interface for C
    rdy_vld_channel< seeSt > cStuffIf;
    // A start done interface
    notify_ack_channel< > startDone;
    // Duplicate interface def
    rdy_vld_channel< seeSt > dupIf;
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > apbReg_uBlockA;
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > apbReg_uBlockB;
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > apbReg_uBlockG;

    //instances contained in block
    std::shared_ptr<blockABase> uBlockA;
    std::shared_ptr<apbDecodeBase> uAPBDecode;
    std::shared_ptr<blockCBase> uBlockC;
    std::shared_ptr<blockBBase> uBlockB;
    std::shared_ptr<blockGBase<blockGGvariant0Config>> uBlockG;

    mixed(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~mixed() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(mixed);

// === Block factory registration (mixed) ===
void register_mixed_variants() {
    instanceFactory::registerBlock("mixed_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<mixed>(blockName, variant, bbMode)); }, "", "mixed");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _mixed_registered = (register_mixed_variants(), 0);
} // namespace
// === End block factory registration ===

mixed::mixed(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("mixed", name(), bbMode)
        ,mixedBase(name(), variant)
        ,aStuffIf("blockB_aStuffIf", "blockA")
        ,cStuffIf("blockC_cStuffIf", "blockA")
        ,startDone("blockB_startDone", "blockA")
        ,dupIf("blockB_dupIf", "blockA")
        ,apbReg_uBlockA("blockA_apbReg_uBlockA", "apbDecode")
        ,apbReg_uBlockB("blockB_apbReg_uBlockB", "apbDecode")
        ,apbReg_uBlockG("blockG_apbReg_uBlockG", "apbDecode")
        ,uBlockA(std::dynamic_pointer_cast<blockABase>(instanceFactory::createInstance(name(), "uBlockA", "blockA", "", "mixed")))
        ,uAPBDecode(std::dynamic_pointer_cast<apbDecodeBase>(instanceFactory::createInstance(name(), "uAPBDecode", "apbDecode", "", "mixed")))
        ,uBlockC(std::dynamic_pointer_cast<blockCBase>(instanceFactory::createInstance(name(), "uBlockC", "blockC", "", "mixed")))
        ,uBlockB(std::dynamic_pointer_cast<blockBBase>(instanceFactory::createInstance(name(), "uBlockB", "blockB", "", "mixed")))
        ,uBlockG(std::dynamic_pointer_cast<blockGBase<blockGGvariant0Config>>(instanceFactory::createInstance(name(), "uBlockG", "blockG", "gvariant0", "mixed")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uAPBDecode->cpu_main(cpu_main);
    // instance to instance connections via channel
    uBlockA->aStuffIf(aStuffIf);
    uBlockB->btod(aStuffIf);
    uBlockA->cStuffIf(cStuffIf);
    uBlockC->see(cStuffIf);
    uBlockA->startDone(startDone);
    uBlockB->startDone(startDone);
    uBlockA->dupIf(dupIf);
    uBlockB->dupIf(dupIf);
    uAPBDecode->apbReg_uBlockA(apbReg_uBlockA);
    uBlockA->apbReg(apbReg_uBlockA);
    uAPBDecode->apbReg_uBlockB(apbReg_uBlockB);
    uBlockB->apbReg(apbReg_uBlockB);
    uAPBDecode->apbReg_uBlockG(apbReg_uBlockG);
    uBlockG->apbReg(apbReg_uBlockG);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    log_.logPrint(std::format("Instance {} test completed.", this->name()), LOG_IMPORTANT );
};

