//

// GENERATED_CODE_PARAM --block=xpCstDut --parent=xpCstBindWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpCstIpVariantConfig.h"

export module xpCstBind.xpCstIp_xpCstDut.registrar;
import xpCstIp_xpCstDut.block;
import xpCstBind.xpCstDut.config;

namespace {
struct _xpCstDut_registrar {
    _xpCstDut_registrar() {
        instanceFactory::registerBlock(
            "xpCstDut_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstDut<xpCstDutDfltConfig>>(blockName, variant, bbMode));
            },
            "dflt", "xpCstBind.xpCstBind_xpCstBindWrap.xpCstIp_xpCstDut");
        instanceFactory::registerBlock(
            "xpCstDut_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstDut<xpCstDutDfltConfig>>(blockName, variant, bbMode));
            },
            "dflt", "xpCstIp");
        instanceFactory::registerBlock(
            "xpCstDut_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstDut<xpCstBind_xpCstDutUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpCstBind.xpCstBind_xpCstBindWrap.xpCstIp_xpCstDut");
        instanceFactory::registerBlock(
            "xpCstDut_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstDut<xpCstBind_xpCstDutUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpCstIp");
    }
};
static _xpCstDut_registrar _xpCstDut_registrar_instance;
} // namespace
// GENERATED_CODE_END
