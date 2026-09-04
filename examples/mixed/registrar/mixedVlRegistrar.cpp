//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=mixed --parent=mixed_tb
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "mixed_hdl_sc_wrapper.h"
#include "Vmixed_hdl_sv_wrapper.h"
#include "mixedVariantConfig.h"

namespace {
struct _mixed_vl_registrar {
    _mixed_vl_registrar() {
        instanceFactory::registerBlock(
            "mixed_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<mixed_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "mixed");
        instanceFactory::registerBlock(
            "mixed_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<mixed_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "mixed");
    }
};
static _mixed_vl_registrar _mixed_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
