//

// GENERATED_CODE_PARAM --block=xpFilter --parent=xpDeparamTop
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpFilterVariantConfig.h"

export module xpDeparam.xpDeparamTop.xpFilter.registrar;
import xpFilter.block;

namespace {
struct _xpFilter_registrar {
    _xpFilter_registrar() {
        instanceFactory::registerBlock(
            "xpFilter_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpFilter<xpFilterV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpDeparam");
    }
};
static _xpFilter_registrar _xpFilter_registrar_instance;
} // namespace
// GENERATED_CODE_END
