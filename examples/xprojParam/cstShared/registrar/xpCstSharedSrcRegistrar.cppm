//

// GENERATED_CODE_PARAM --block=xpCstSharedSrc --parent=xpCstSharedWrap/../../yaml/xpCstSharedTop.yaml
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module xpCstShared.xpCstShared_xpCstSharedSrc.registrar;
import xpCstShared_xpCstSharedSrc.block;
import xpCstShared.xpCstSharedSrc.config;

namespace {
struct _xpCstSharedSrc_registrar {
    _xpCstSharedSrc_registrar() {
        instanceFactory::registerBlock(
            "xpCstSharedSrc_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstSharedSrc<xpCstShared_xpCstSharedSrcUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpCstShared");
        instanceFactory::registerBlock(
            "xpCstSharedSrc_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstSharedSrc<xpCstShared_xpCstSharedSrcUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpCstShared.xpCstShared_xpCstSharedWrap.xpCstShared_xpCstSharedSrc");
    }
};
static _xpCstSharedSrc_registrar _xpCstSharedSrc_registrar_instance;
} // namespace
// GENERATED_CODE_END
