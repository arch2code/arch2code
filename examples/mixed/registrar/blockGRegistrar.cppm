//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockG --parent=mixed
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "mixedVariantConfig.h"

export module mixed.mixed.blockG.registrar;
import mixed_blockG.block;

namespace {
struct _blockG_registrar {
    _blockG_registrar() {
        instanceFactory::registerBlock(
            "blockG_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockG<blockGGvariant0Config>>(blockName, variant, bbMode));
            },
            "gvariant0", "mixed");
    }
};
static _blockG_registrar _blockG_registrar_instance;
} // namespace
// GENERATED_CODE_END
