//

// GENERATED_CODE_PARAM --block=xpCstSrcOwn --parent=xpCstBindWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpCstSupVariantConfig.h"

export module xpCstBind.xpCstBind_xpCstSrcOwn.registrar;
import xpCstBind_xpCstSrcOwn.block;

namespace {
struct _xpCstSrcOwn_registrar {
    _xpCstSrcOwn_registrar() {
        instanceFactory::registerBlock(
            "xpCstSrcOwn_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstSrcOwn<xpCstSrcOwnUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpCstBind");
        instanceFactory::registerBlock(
            "xpCstSrcOwn_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstSrcOwn<xpCstSrcOwnUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpCstBind.xpCstBind_xpCstBindWrap.xpCstBind_xpCstSrcOwn");
    }
};
static _xpCstSrcOwn_registrar _xpCstSrcOwn_registrar_instance;
} // namespace
// GENERATED_CODE_END
