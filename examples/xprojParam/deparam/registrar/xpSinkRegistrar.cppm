//

// GENERATED_CODE_PARAM --block=xpSink --parent=xpDeparamTop
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpSinkVariantConfig.h"

export module xpDeparam.xpDeparamTop.xpSink.registrar;
import xpSink.block;

namespace {
struct _xpSink_registrar {
    _xpSink_registrar() {
        instanceFactory::registerBlock(
            "xpSink_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpSink<xpSinkV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpDeparam");
    }
};
static _xpSink_registrar _xpSink_registrar_instance;
} // namespace
// GENERATED_CODE_END
