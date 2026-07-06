//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=core
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "core.h"
#include "genBase.h"
#include "leafBase.h"
SC_HAS_PROCESS(core);

// === Block factory registration (core) ===
void register_core_variants() {
    instanceFactory::registerBlock("core_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<core>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _core_registered = (register_core_variants(), 0);
} // namespace
// === End block factory registration ===

core::core(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("core", name(), bbMode)
        ,coreBase(name(), variant)
        ,dOut_0("leaf_dOut_0", "gen")
        ,dOut_1("leaf_dOut_1", "leaf")
        ,dOut_2("gen_dOut_2", "leaf")
        ,u_gen(std::dynamic_pointer_cast<genBase>(instanceFactory::createInstance(name(), "u_gen", "gen", "")))
        ,u_leaf0(std::dynamic_pointer_cast<leafBase>(instanceFactory::createInstance(name(), "u_leaf0", "leaf", "")))
        ,u_leaf1(std::dynamic_pointer_cast<leafBase>(instanceFactory::createInstance(name(), "u_leaf1", "leaf", "")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    u_gen->dOut(dOut_0);
    u_leaf0->dIn(dOut_0);
    u_leaf0->dOut(dOut_1);
    u_leaf1->dIn(dOut_1);
    u_leaf1->dOut(dOut_2);
    u_gen->dIn(dOut_2);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

