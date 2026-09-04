//

// GENERATED_CODE_PARAM --block=xpGain --parent=xpSharedTop
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpGainVariantConfig.h"

export module xpShared.xpGain.registrar;
import xpGain.block;

namespace {
struct _xpGain_registrar {
    _xpGain_registrar() {
        instanceFactory::registerBlock(
            "xpGain_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpGain<xpGainV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpGain");
        instanceFactory::registerBlock(
            "xpGain_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpGain<xpGainV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpShared.xpShared_xpSharedTop.xpGain");
    }
};
static _xpGain_registrar _xpGain_registrar_instance;
} // namespace
// GENERATED_CODE_END
