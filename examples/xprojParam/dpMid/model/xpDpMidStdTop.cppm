//

// GENERATED_CODE_PARAM --block=xpDpMidStdTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "xpDpLeafVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpDpMid_xpDpMidStdTop.block;
import xpDpMid_xpDpMidStdTop.base;
import xpDpMid_xpDpMidStdWrap.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
export SC_MODULE(xpDpMidStdTop), public blockBase, public xpDpMidStdTopBase
{
private:

public:
    //instances contained in block
    std::shared_ptr<xpDpMidStdWrapBase> uStdWrap;

    xpDpMidStdTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpDpMidStdTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpDpMidStdTop);

// === Block factory registration (xpDpMidStdTop) ===
void register_xpDpMidStdTop_variants() {
    instanceFactory::registerBlock("xpDpMidStdTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpMidStdTop>(blockName, variant, bbMode)); }, "", "xpDpMid");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpDpMidStdTop_registered = (register_xpDpMidStdTop_variants(), 0);
} // namespace
// === End block factory registration ===

xpDpMidStdTop::xpDpMidStdTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpDpMidStdTop", name(), bbMode)
        ,xpDpMidStdTopBase(name(), variant)
        ,uStdWrap(std::dynamic_pointer_cast<xpDpMidStdWrapBase>(instanceFactory::createInstance(name(), "uStdWrap", "xpDpMidStdWrap", "", "xpDpMid")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

