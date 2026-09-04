//

// GENERATED_CODE_PARAM --block=xpMtxDstPar --parent=xpMtxElectWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpMtxIpVariantConfig.h"

export module xpMtxElect.xpMtxIp_xpMtxDstPar.registrar;
import xpMtxIp_xpMtxDstPar.block;

namespace {
struct _xpMtxDstPar_registrar {
    _xpMtxDstPar_registrar() {
        instanceFactory::registerBlock(
            "xpMtxDstPar_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpMtxDstPar<xpMtxDstParV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpMtxElect.xpMtxElect_xpMtxElectWrap.xpMtxIp_xpMtxDstPar");
        instanceFactory::registerBlock(
            "xpMtxDstPar_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpMtxDstPar<xpMtxDstParV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpMtxIp");
    }
};
static _xpMtxDstPar_registrar _xpMtxDstPar_registrar_instance;
} // namespace
// GENERATED_CODE_END
