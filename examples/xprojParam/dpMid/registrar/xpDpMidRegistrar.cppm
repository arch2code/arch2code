//

// GENERATED_CODE_PARAM --block=xpDpMid --parent=xpDpMidStdTop
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpDpLeafVariantConfig.h"

export module xpDpMid.xpDpMidStdTop.xpDpMid.registrar;
import xpDpMid.block;
import xpDpMid.xpDpMid.config;

namespace {
struct _xpDpMid_registrar {
    _xpDpMid_registrar() {
        instanceFactory::registerBlock(
            "xpDpMid_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpMid<xpDpMid_xpDpMidStdConfig>>(blockName, variant, bbMode));
            },
            "std", "xpDpMid");
    }
};
static _xpDpMid_registrar _xpDpMid_registrar_instance;
} // namespace
// GENERATED_CODE_END
