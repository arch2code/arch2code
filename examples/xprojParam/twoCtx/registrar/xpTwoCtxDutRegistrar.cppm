//

// GENERATED_CODE_PARAM --block=xpTwoCtxDut --parent=xpTwoCtxWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module xpTwoCtx.xpTwoCtx_xpTwoCtxDut.registrar;
import xpTwoCtx_xpTwoCtxDut.block;
import xpTwoCtx.xpTwoCtxDut.config;

namespace {
struct _xpTwoCtxDut_registrar {
    _xpTwoCtxDut_registrar() {
        instanceFactory::registerBlock(
            "xpTwoCtxDut_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpTwoCtxDut<xpTwoCtx_xpTwoCtxDutTwoctxConfig>>(blockName, variant, bbMode));
            },
            "twoctx", "xpTwoCtx");
        instanceFactory::registerBlock(
            "xpTwoCtxDut_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpTwoCtxDut<xpTwoCtx_xpTwoCtxDutTwoctxConfig>>(blockName, variant, bbMode));
            },
            "twoctx", "xpTwoCtx.xpTwoCtx_xpTwoCtxWrap.xpTwoCtx_xpTwoCtxDut");
    }
};
static _xpTwoCtxDut_registrar _xpTwoCtxDut_registrar_instance;
} // namespace
// GENERATED_CODE_END
