//

// GENERATED_CODE_PARAM --block=xpCstUseChk --parent=xpCstUseWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpCstIpVariantConfig.h"

export module xpCstUse.xpCstUse_xpCstUseChk.registrar;
import xpCstUse_xpCstUseChk.block;
import xpCstUse.xpCstUseChk.config;

namespace {
struct _xpCstUseChk_registrar {
    _xpCstUseChk_registrar() {
        instanceFactory::registerBlock(
            "xpCstUseChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstUseChk<xpCstUse_xpCstUseChkUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpCstUse");
        instanceFactory::registerBlock(
            "xpCstUseChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstUseChk<xpCstUse_xpCstUseChkUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpCstUse.xpCstUse_xpCstUseWrap.xpCstUse_xpCstUseChk");
    }
};
static _xpCstUseChk_registrar _xpCstUseChk_registrar_instance;
} // namespace
// GENERATED_CODE_END
