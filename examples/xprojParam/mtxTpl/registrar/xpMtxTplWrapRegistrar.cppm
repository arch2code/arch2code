//

// GENERATED_CODE_PARAM --block=xpMtxTplWrap --parent=xpMtxTplTop
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpMtxIpVariantConfig.h"
#include "xpMtxTplTopVariantConfig.h"

export module xpMtxTpl.xpMtxTplTop.xpMtxTplWrap.registrar;
import xpMtxTpl_xpMtxTplWrap.block;

namespace {
struct _xpMtxTplWrap_registrar {
    _xpMtxTplWrap_registrar() {
        instanceFactory::registerBlock(
            "xpMtxTplWrap_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpMtxTplWrap<xpMtxTplWrapV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpMtxTpl");
    }
};
static _xpMtxTplWrap_registrar _xpMtxTplWrap_registrar_instance;
} // namespace
// GENERATED_CODE_END
