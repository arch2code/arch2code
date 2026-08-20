//

// GENERATED_CODE_PARAM --block=xpInhDrv --parent=xpInhWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpInhContVariantConfig.h"

export module xpInhVar.xpInhWrap.xpInhDrv.registrar;
import xpInhVar_xpInhDrv.block;

namespace {
struct _xpInhDrv_registrar {
    _xpInhDrv_registrar() {
        instanceFactory::registerBlock(
            "xpInhDrv_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpInhDrv<xpInhDrvDrvConfig>>(blockName, variant, bbMode));
            },
            "drv", "xpInhVar");
    }
};
static _xpInhDrv_registrar _xpInhDrv_registrar_instance;
} // namespace
// GENERATED_CODE_END
