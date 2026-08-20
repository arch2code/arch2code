//

// GENERATED_CODE_PARAM --block=xpCstSrcInc --parent=xpCstBindWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpCstIpVariantConfig.h"

export module xpCstBind.xpCstBindWrap.xpCstSrcInc.registrar;
import xpCstBind_xpCstSrcInc.block;
import xpCstBind.xpCstSrcInc.config;

namespace {
struct _xpCstSrcInc_registrar {
    _xpCstSrcInc_registrar() {
        instanceFactory::registerBlock(
            "xpCstSrcInc_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstSrcInc<xpCstBind_xpCstSrcIncDfltConfig>>(blockName, variant, bbMode));
            },
            "dflt", "xpCstBind");
    }
};
static _xpCstSrcInc_registrar _xpCstSrcInc_registrar_instance;
} // namespace
// GENERATED_CODE_END
