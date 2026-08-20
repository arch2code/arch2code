//

// GENERATED_CODE_PARAM --block=xpDpMidDrv --parent=xpDpMidStdTop
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpDpLeafVariantConfig.h"

export module xpDpMid.xpDpMidStdTop.xpDpMidDrv.registrar;
import xpDpMid_xpDpMidDrv.block;
import xpDpMid.xpDpMidDrv.config;

namespace {
struct _xpDpMidDrv_registrar {
    _xpDpMidDrv_registrar() {
        instanceFactory::registerBlock(
            "xpDpMidDrv_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpMidDrv<xpDpMid_xpDpMidDrvStdConfig>>(blockName, variant, bbMode));
            },
            "std", "xpDpMid");
    }
};
static _xpDpMidDrv_registrar _xpDpMidDrv_registrar_instance;
} // namespace
// GENERATED_CODE_END
