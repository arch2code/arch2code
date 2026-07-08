//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "mixedVariantConfig.h"

// GENERATED_CODE_PARAM --block=mixed
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "mixed.h"
import blockA.base;
import apbDecode.base;
import blockC.base;
import blockB.base;
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
        ,uBlockA(std::dynamic_pointer_cast<blockABase>(instanceFactory::createInstance(name(), "uBlockA", "blockA", "", "mixed")))
        ,uAPBDecode(std::dynamic_pointer_cast<apbDecodeBase>(instanceFactory::createInstance(name(), "uAPBDecode", "apbDecode", "", "mixed")))
        ,uBlockC(std::dynamic_pointer_cast<blockCBase>(instanceFactory::createInstance(name(), "uBlockC", "blockC", "", "mixed")))
        ,uBlockB(std::dynamic_pointer_cast<blockBBase>(instanceFactory::createInstance(name(), "uBlockB", "blockB", "", "mixed")))
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
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END

    log_.logPrint(std::format("Instance {} test completed.", this->name()), LOG_IMPORTANT );

}
