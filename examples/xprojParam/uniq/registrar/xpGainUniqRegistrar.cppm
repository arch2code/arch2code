//

// GENERATED_CODE_PARAM --block=xpGainUniq --parent=xpUniqTop
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpGainUniqVariantConfig.h"

export module xpUniq.xpUniqTop.xpGainUniq.registrar;
import xpGain_xpGainUniq.block;

namespace {
struct _xpGainUniq_registrar {
    _xpGainUniq_registrar() {
        instanceFactory::registerBlock(
            "xpGainUniq_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpGainUniq<xpGainUniqV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpUniq");
    }
};
static _xpGainUniq_registrar _xpGainUniq_registrar_instance;
} // namespace
// GENERATED_CODE_END
