// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE


// GENERATED_CODE_PARAM --block=secondBlock
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "secondBlock.h"
#include "secondSubABase.h"
#include "secondSubBBase.h"
SC_HAS_PROCESS(secondBlock);

// === Block factory registration (secondBlock) ===
void register_secondBlock_variants() {
    instanceFactory::registerBlock("secondBlock_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<secondBlock>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _secondBlock_registered = (register_secondBlock_variants(), 0);
} // namespace
// === End block factory registration ===

secondBlock::secondBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("secondBlock", name(), bbMode)
        ,secondBlockBase(name(), variant)
        ,test("secondSubB_test", "secondSubA")
        ,uSecondSubA(std::dynamic_pointer_cast<secondSubABase>(instanceFactory::createInstance(name(), "uSecondSubA", "secondSubA", "")))
        ,uSecondSubB(std::dynamic_pointer_cast<secondSubBBase>(instanceFactory::createInstance(name(), "uSecondSubB", "secondSubB", "")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uSecondSubA->primary(primary);
    uSecondSubB->beta(beta);
    // instance to instance connections via channel
    uSecondSubA->test(test);
    uSecondSubB->test(test);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END

}


