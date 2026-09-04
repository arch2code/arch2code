//

// GENERATED_CODE_PARAM --block=xpFilterUniq --parent=xpUniqTop
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpFilterUniqVariantConfig.h"

export module xpUniq.xpFilter_xpFilterUniq.registrar;
import xpFilter_xpFilterUniq.block;

namespace {
struct _xpFilterUniq_registrar {
    _xpFilterUniq_registrar() {
        instanceFactory::registerBlock(
            "xpFilterUniq_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpFilterUniq<xpFilterUniqV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpFilter");
        instanceFactory::registerBlock(
            "xpFilterUniq_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpFilterUniq<xpFilterUniqV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpUniq.xpUniq_xpUniqTop.xpFilter_xpFilterUniq");
    }
};
static _xpFilterUniq_registrar _xpFilterUniq_registrar_instance;
} // namespace
// GENERATED_CODE_END
