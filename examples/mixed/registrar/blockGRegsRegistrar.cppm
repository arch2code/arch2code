//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockGRegs --parent=blockG
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "mixedVariantConfig.h"

export module mixed.blockG.blockGRegs.registrar;
import mixed_blockGRegs.block;

namespace {
struct _blockGRegs_registrar {
    _blockGRegs_registrar() {
        instanceFactory::registerBlock(
            "blockGRegs_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockGRegs<mixedDefaultConfig>>(blockName, variant, bbMode));
            },
            "", "mixed");
    }
};
static _blockGRegs_registrar _blockGRegs_registrar_instance;
} // namespace
// GENERATED_CODE_END
