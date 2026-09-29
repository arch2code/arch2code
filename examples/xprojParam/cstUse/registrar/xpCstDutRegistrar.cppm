//

// GENERATED_CODE_PARAM --block=xpCstDut --parent=xpCstUseWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module xpCstUse.xpCstIp_xpCstDut.registrar;
import xpCstIp_xpCstDut.block;
import xpCstUse.xpCstDut.config;

namespace {
struct _xpCstDut_registrar {
    _xpCstDut_registrar() {
        instanceFactory::registerBlock(
            "xpCstDut_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstDut<xpCstUse_xpCstDutUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpCstIp");
        instanceFactory::registerBlock(
            "xpCstDut_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstDut<xpCstUse_xpCstDutUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpCstUse.xpCstUse_xpCstUseWrap.xpCstIp_xpCstDut");
    }
};
static _xpCstDut_registrar _xpCstDut_registrar_instance;
} // namespace
// GENERATED_CODE_END
