//

// GENERATED_CODE_PARAM --block=xpSinkShared --parent=xpSharedTop
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpGainVariantConfig.h"

export module xpShared.xpSharedTop.xpSinkShared.registrar;
import xpSinkShared.block;

namespace {
struct _xpSinkShared_registrar {
    _xpSinkShared_registrar() {
        instanceFactory::registerBlock(
            "xpSinkShared_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpSinkShared<xpGainDefaultConfig>>(blockName, variant, bbMode));
            },
            "v0", "xpShared");
    }
};
static _xpSinkShared_registrar _xpSinkShared_registrar_instance;
} // namespace
// GENERATED_CODE_END
