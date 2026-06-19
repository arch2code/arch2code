// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE
#include <memory>
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=top
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "top.h"
#include "cpu_base.h"
#include "someRapper_base.h"
SC_HAS_PROCESS(top);

// === Block factory registration (top) ===
void force_link_top() {}

void register_top_variants() {
    instanceFactory::registerBlock("top_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<top>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _top_registered = (register_top_variants(), 0);
} // namespace
// === End block factory registration ===

top::top(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("top", name(), bbMode)
        ,topBase(name(), variant)
        ,apbReg("someRapper_apbReg", "cpu")
        ,uCPU(std::dynamic_pointer_cast<cpuBase>((force_link_cpu(), instanceFactory::createInstance(name(), "uCPU", "cpu", ""))))
        ,uSomeRapper(std::dynamic_pointer_cast<someRapperBase>((force_link_someRapper(), instanceFactory::createInstance(name(), "uSomeRapper", "someRapper", ""))))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uCPU->apbReg(apbReg);
    uSomeRapper->apbReg(apbReg);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    //auto baseInstance = instanceFactory::createInstance("uProducer");
    //uProducer2 = (producer *) baseInstance.get();
}
