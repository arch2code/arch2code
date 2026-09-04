//

// GENERATED_CODE_PARAM --block=xpDpWrap --parent=xpDpTop
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpDpLeafVariantConfig.h"

export module xpDpTop.xpDpTop_xpDpWrap.registrar;
import xpDpTop_xpDpWrap.block;
import xpDpTop.xpDpWrap.config;

namespace {
struct _xpDpWrap_registrar {
    _xpDpWrap_registrar() {
        instanceFactory::registerBlock(
            "xpDpWrap_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpWrap<xpDpTop_xpDpWrapCustomerConfig>>(blockName, variant, bbMode));
            },
            "customer", "xpDpTop");
        instanceFactory::registerBlock(
            "xpDpWrap_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpWrap<xpDpTop_xpDpWrapCustomerConfig>>(blockName, variant, bbMode));
            },
            "customer", "xpDpTop.xpDpTop.xpDpTop_xpDpWrap");
    }
};
static _xpDpWrap_registrar _xpDpWrap_registrar_instance;
} // namespace
// GENERATED_CODE_END
