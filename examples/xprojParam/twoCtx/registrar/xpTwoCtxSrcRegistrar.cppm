//

// GENERATED_CODE_PARAM --block=xpTwoCtxSrc --parent=xpTwoCtxWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module xpTwoCtx.xpTwoCtx_xpTwoCtxSrc.registrar;
import xpTwoCtx_xpTwoCtxSrc.block;
import xpTwoCtx.xpTwoCtxSrc.config;

namespace {
struct _xpTwoCtxSrc_registrar {
    _xpTwoCtxSrc_registrar() {
        instanceFactory::registerBlock(
            "xpTwoCtxSrc_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpTwoCtxSrc<xpTwoCtx_xpTwoCtxSrcTwoctxConfig>>(blockName, variant, bbMode));
            },
            "twoctx", "xpTwoCtx");
        instanceFactory::registerBlock(
            "xpTwoCtxSrc_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpTwoCtxSrc<xpTwoCtx_xpTwoCtxSrcTwoctxConfig>>(blockName, variant, bbMode));
            },
            "twoctx", "xpTwoCtx.xpTwoCtx_xpTwoCtxWrap.xpTwoCtx_xpTwoCtxSrc");
    }
};
static _xpTwoCtxSrc_registrar _xpTwoCtxSrc_registrar_instance;
} // namespace
// GENERATED_CODE_END
