//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockG --parent=mixed
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module mixed.mixed_blockG.registrar;
import mixed_blockG.block;
import mixed.blockG.config;

namespace {
struct _blockG_registrar {
    _blockG_registrar() {
        instanceFactory::registerBlock(
            "blockG_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockG<mixed_blockGGvariant0Config>>(blockName, variant, bbMode));
            },
            "gvariant0", "mixed");
        instanceFactory::registerBlock(
            "blockG_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockG<mixed_blockGGvariant0Config>>(blockName, variant, bbMode));
            },
            "gvariant0", "mixed.mixed.mixed_blockG");
    }
};
static _blockG_registrar _blockG_registrar_instance;
} // namespace
// GENERATED_CODE_END
