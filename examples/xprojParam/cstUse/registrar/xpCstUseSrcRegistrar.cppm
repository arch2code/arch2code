//

// GENERATED_CODE_PARAM --block=xpCstUseSrc --parent=xpCstUseWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpCstIpVariantConfig.h"

export module xpCstUse.xpCstUseWrap.xpCstUseSrc.registrar;
import xpCstUse_xpCstUseSrc.block;
import xpCstUse.xpCstUseSrc.config;

namespace {
struct _xpCstUseSrc_registrar {
    _xpCstUseSrc_registrar() {
        instanceFactory::registerBlock(
            "xpCstUseSrc_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstUseSrc<xpCstUse_xpCstUseSrcUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpCstUse");
    }
};
static _xpCstUseSrc_registrar _xpCstUseSrc_registrar_instance;
} // namespace
// GENERATED_CODE_END
