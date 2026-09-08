//

// GENERATED_CODE_PARAM --block=xpMtxDstPar --parent=xpMtxLitWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module xpMtxLit.xpMtxIp_xpMtxDstPar.registrar;
import xpMtxIp_xpMtxDstPar.block;
import xpMtxIp.xpMtxDstPar.config;

namespace {
struct _xpMtxDstPar_registrar {
    _xpMtxDstPar_registrar() {
        instanceFactory::registerBlock(
            "xpMtxDstPar_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpMtxDstPar<xpMtxIp_xpMtxDstParV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpMtxIp");
        instanceFactory::registerBlock(
            "xpMtxDstPar_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpMtxDstPar<xpMtxIp_xpMtxDstParV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpMtxLit.xpMtxLit_xpMtxLitWrap.xpMtxIp_xpMtxDstPar");
    }
};
static _xpMtxDstPar_registrar _xpMtxDstPar_registrar_instance;
} // namespace
// GENERATED_CODE_END
