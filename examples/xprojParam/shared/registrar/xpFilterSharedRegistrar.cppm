//

// GENERATED_CODE_PARAM --block=xpFilterShared --parent=xpSharedTop
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpGainVariantConfig.h"

export module xpShared.xpSharedTop.xpFilterShared.registrar;
import xpFilterShared.block;

namespace {
struct _xpFilterShared_registrar {
    _xpFilterShared_registrar() {
        instanceFactory::registerBlock(
            "xpFilterShared_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpFilterShared<xpGainDefaultConfig>>(blockName, variant, bbMode));
            },
            "v0", "xpShared");
    }
};
static _xpFilterShared_registrar _xpFilterShared_registrar_instance;
} // namespace
// GENERATED_CODE_END
