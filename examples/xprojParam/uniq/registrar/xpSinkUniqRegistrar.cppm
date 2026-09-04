//

// GENERATED_CODE_PARAM --block=xpSinkUniq --parent=xpUniqTop
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpSinkUniqVariantConfig.h"

export module xpUniq.xpSink_xpSinkUniq.registrar;
import xpSink_xpSinkUniq.block;

namespace {
struct _xpSinkUniq_registrar {
    _xpSinkUniq_registrar() {
        instanceFactory::registerBlock(
            "xpSinkUniq_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpSinkUniq<xpSinkUniqV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpSink");
        instanceFactory::registerBlock(
            "xpSinkUniq_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpSinkUniq<xpSinkUniqV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpUniq.xpUniq_xpUniqTop.xpSink_xpSinkUniq");
    }
};
static _xpSinkUniq_registrar _xpSinkUniq_registrar_instance;
} // namespace
// GENERATED_CODE_END
