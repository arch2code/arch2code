//

// GENERATED_CODE_PARAM --block=xpSharedTop --parent=xpSharedTop_tb
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpGainVariantConfig.h"
#include "xpSharedTop.h"

export module xpShared.xpSharedTop_tb.xpSharedTop.registrar;

namespace {
struct _xpSharedTop_registrar {
    _xpSharedTop_registrar() {
        instanceFactory::registerBlock(
            "xpSharedTop_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpSharedTop>(blockName, variant, bbMode));
            },
            "", "xpShared");
    }
};
static _xpSharedTop_registrar _xpSharedTop_registrar_instance;
} // namespace
// GENERATED_CODE_END
