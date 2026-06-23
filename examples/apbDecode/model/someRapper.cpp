//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=someRapper
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "someRapper.h"
#include "apbDecodeBase.h"
#include "blockABase.h"
#include "blockBBase.h"
SC_HAS_PROCESS(someRapper);

// === Block factory registration (someRapper) ===
void force_link_someRapper() {}

void register_someRapper_variants() {
    instanceFactory::registerBlock("someRapper_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<someRapper>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _someRapper_registered = (register_someRapper_variants(), 0);
} // namespace
// === End block factory registration ===

someRapper::someRapper(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("someRapper", name(), bbMode)
        ,someRapperBase(name(), variant)
        ,apbReg_uBlockA("blockA_apbReg_uBlockA", "apbDecode")
        ,apbReg_uBlockB("blockB_apbReg_uBlockB", "apbDecode")
        ,uAPBDecode(std::dynamic_pointer_cast<apbDecodeBase>((force_link_apbDecode(), instanceFactory::createInstance(name(), "uAPBDecode", "apbDecode", ""))))
        ,uBlockA(std::dynamic_pointer_cast<blockABase>((force_link_blockA(), instanceFactory::createInstance(name(), "uBlockA", "blockA", ""))))
        ,uBlockB(std::dynamic_pointer_cast<blockBBase>((force_link_blockB(), instanceFactory::createInstance(name(), "uBlockB", "blockB", ""))))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uAPBDecode->apbReg(apbReg);
    // instance to instance connections via channel
    uAPBDecode->apbReg_uBlockA(apbReg_uBlockA);
    uBlockA->apbReg(apbReg_uBlockA);
    uAPBDecode->apbReg_uBlockB(apbReg_uBlockB);
    uBlockB->apbReg(apbReg_uBlockB);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

