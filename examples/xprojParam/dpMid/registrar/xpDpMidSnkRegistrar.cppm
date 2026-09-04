//

// GENERATED_CODE_PARAM --block=xpDpMidSnk --parent=xpDpMidStdTop
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpDpLeafVariantConfig.h"

export module xpDpMid.xpDpMid_xpDpMidSnk.registrar;
import xpDpMid_xpDpMidSnk.block;
import xpDpMid.xpDpMidSnk.config;

namespace {
struct _xpDpMidSnk_registrar {
    _xpDpMidSnk_registrar() {
        instanceFactory::registerBlock(
            "xpDpMidSnk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpMidSnk<xpDpMid_xpDpMidSnkStdConfig>>(blockName, variant, bbMode));
            },
            "std", "xpDpMid");
        instanceFactory::registerBlock(
            "xpDpMidSnk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpMidSnk<xpDpMid_xpDpMidSnkStdConfig>>(blockName, variant, bbMode));
            },
            "std", "xpDpMid.xpDpMid_xpDpMidStdWrap.xpDpMid_xpDpMidSnk");
    }
};
static _xpDpMidSnk_registrar _xpDpMidSnk_registrar_instance;
} // namespace
// GENERATED_CODE_END
