//

// GENERATED_CODE_PARAM --block=vliTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "vliContVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module vlInh_vliTop.block;
import vlInh_vliTop.base;
import vlInh_vliWrap.base;
import vlInh_vliCont;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace vlInh_vliCont_ns;
export SC_MODULE(vliTop), public blockBase, public vliTopBase
{
private:

public:
    //instances contained in block
    std::shared_ptr<vliWrapBase> uWrap;

    vliTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~vliTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(vliTop);

// === Block factory registration (vliTop) ===
void register_vliTop_variants() {
    instanceFactory::registerBlock("vliTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliTop>(blockName, variant, bbMode)); }, "", "vlInh");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _vliTop_registered = (register_vliTop_variants(), 0);
} // namespace
// === End block factory registration ===

vliTop::vliTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("vliTop", name(), bbMode)
        ,vliTopBase(name(), variant)
        ,uWrap(std::dynamic_pointer_cast<vliWrapBase>(instanceFactory::createInstance(name(), "uWrap", "vliWrap", "", "vlInh")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

