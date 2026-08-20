//

// GENERATED_CODE_PARAM --block=xpTwoCtxBare --parent=xpTwoCtxWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpTwoCtxVariantConfig.h"

export module xpTwoCtx.xpTwoCtxWrap.xpTwoCtxBare.registrar;
import xpTwoCtx_xpTwoCtxBare.block;

namespace {
struct _xpTwoCtxBare_registrar {
    _xpTwoCtxBare_registrar() {
        instanceFactory::registerBlock(
            "xpTwoCtxBare_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpTwoCtxBare<xpTwoCtxBareTwoctxConfig>>(blockName, variant, bbMode));
            },
            "twoctx", "xpTwoCtx");
    }
};
static _xpTwoCtxBare_registrar _xpTwoCtxBare_registrar_instance;
} // namespace
// GENERATED_CODE_END
