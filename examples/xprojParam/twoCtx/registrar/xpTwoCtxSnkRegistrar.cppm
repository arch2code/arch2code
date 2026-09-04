//

// GENERATED_CODE_PARAM --block=xpTwoCtxSnk --parent=xpTwoCtxWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpTwoCtxVariantConfig.h"

export module xpTwoCtx.xpTwoCtx_xpTwoCtxSnk.registrar;
import xpTwoCtx_xpTwoCtxSnk.block;

namespace {
struct _xpTwoCtxSnk_registrar {
    _xpTwoCtxSnk_registrar() {
        instanceFactory::registerBlock(
            "xpTwoCtxSnk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpTwoCtxSnk<xpTwoCtxSnkTwoctxConfig>>(blockName, variant, bbMode));
            },
            "twoctx", "xpTwoCtx");
        instanceFactory::registerBlock(
            "xpTwoCtxSnk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpTwoCtxSnk<xpTwoCtxSnkTwoctxConfig>>(blockName, variant, bbMode));
            },
            "twoctx", "xpTwoCtx.xpTwoCtx_xpTwoCtxWrap.xpTwoCtx_xpTwoCtxSnk");
    }
};
static _xpTwoCtxSnk_registrar _xpTwoCtxSnk_registrar_instance;
} // namespace
// GENERATED_CODE_END
