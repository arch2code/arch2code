//

// GENERATED_CODE_PARAM --block=xviMidTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "xviLeafVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xviMid_xviMidTop.block;
import xviMid_xviMidTop.base;
import xviMid.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
export SC_MODULE(xviMidTop), public blockBase, public xviMidTopBase
{
private:

public:
    //instances contained in block
    std::shared_ptr<xviMidBase> uMid;

    xviMidTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xviMidTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xviMidTop);

// === Block factory registration (xviMidTop) ===
void register_xviMidTop_variants() {
    instanceFactory::registerBlock("xviMidTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviMidTop>(blockName, variant, bbMode)); }, "", "xviMid");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xviMidTop_registered = (register_xviMidTop_variants(), 0);
} // namespace
// === End block factory registration ===

xviMidTop::xviMidTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xviMidTop", name(), bbMode)
        ,xviMidTopBase(name(), variant)
        ,uMid(std::dynamic_pointer_cast<xviMidBase>(instanceFactory::createInstance(name(), "uMid", "xviMid", "", "xviMid")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

