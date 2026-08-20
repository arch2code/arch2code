//

// GENERATED_CODE_PARAM --block=xpMtxSrcPar --parent=xpMtxElectWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpMtxIpVariantConfig.h"

export module xpMtxElect.xpMtxElectWrap.xpMtxSrcPar.registrar;
import xpMtxIp_xpMtxSrcPar.block;

namespace {
struct _xpMtxSrcPar_registrar {
    _xpMtxSrcPar_registrar() {
        instanceFactory::registerBlock(
            "xpMtxSrcPar_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpMtxSrcPar<xpMtxSrcParV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpMtxElect");
    }
};
static _xpMtxSrcPar_registrar _xpMtxSrcPar_registrar_instance;
} // namespace
// GENERATED_CODE_END
