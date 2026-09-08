//

// GENERATED_CODE_PARAM --block=xpGain --parent=xpDeparamTop
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module xpDeparam.xpGain.registrar;
import xpGain.block;
import xpGain.xpGain.config;

namespace {
struct _xpGain_registrar {
    _xpGain_registrar() {
        instanceFactory::registerBlock(
            "xpGain_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpGain<xpGain_xpGainV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpDeparam.xpDeparam_xpDeparamTop.xpGain");
        instanceFactory::registerBlock(
            "xpGain_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpGain<xpGain_xpGainV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpGain");
    }
};
static _xpGain_registrar _xpGain_registrar_instance;
} // namespace
// GENERATED_CODE_END
