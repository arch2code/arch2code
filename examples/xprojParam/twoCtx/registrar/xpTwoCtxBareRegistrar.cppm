//

// GENERATED_CODE_PARAM --block=xpTwoCtxBare --parent=xpTwoCtxWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module xpTwoCtx.xpTwoCtx_xpTwoCtxBare.registrar;
import xpTwoCtx_xpTwoCtxBare.block;
import xpTwoCtx.xpTwoCtxBare.config;

namespace {
struct _xpTwoCtxBare_registrar {
    _xpTwoCtxBare_registrar() {
        instanceFactory::registerBlock(
            "xpTwoCtxBare_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpTwoCtxBare<xpTwoCtx_xpTwoCtxBareTwoctxConfig>>(blockName, variant, bbMode));
            },
            "twoctx", "xpTwoCtx");
        instanceFactory::registerBlock(
            "xpTwoCtxBare_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpTwoCtxBare<xpTwoCtx_xpTwoCtxBareTwoctxConfig>>(blockName, variant, bbMode));
            },
            "twoctx", "xpTwoCtx.xpTwoCtx_xpTwoCtxWrap.xpTwoCtx_xpTwoCtxBare");
    }
};
static _xpTwoCtxBare_registrar _xpTwoCtxBare_registrar_instance;
} // namespace
// GENERATED_CODE_END
