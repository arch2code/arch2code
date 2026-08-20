//

// GENERATED_CODE_PARAM --block=xpDpSrc --parent=xpDpWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpDpLeafVariantConfig.h"

export module xpDpTop.xpDpWrap.xpDpSrc.registrar;
import xpDpTop_xpDpSrc.block;
import xpDpTop.xpDpSrc.config;

namespace {
struct _xpDpSrc_registrar {
    _xpDpSrc_registrar() {
        instanceFactory::registerBlock(
            "xpDpSrc_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpSrc<xpDpTop_xpDpSrcCustomerConfig>>(blockName, variant, bbMode));
            },
            "customer", "xpDpTop");
    }
};
static _xpDpSrc_registrar _xpDpSrc_registrar_instance;
} // namespace
// GENERATED_CODE_END
