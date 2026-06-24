//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockF
// GENERATED_CODE_BEGIN --template=blockRegistrar
#include "instanceFactory.h"
#include "blockBase.h"
#include "mixedVariantConfig.h"
#include "blockF.h"

namespace {
struct _blockF_registrar {
    _blockF_registrar() {
        instanceFactory::registerBlock(
            "blockF_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockF<mixedDefaultConfig>>(blockName, variant, bbMode));
            },
            "variant0");
        instanceFactory::registerBlock(
            "blockF_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockF<blockFVariant1Config>>(blockName, variant, bbMode));
            },
            "variant1");
    }
};
static _blockF_registrar _blockF_registrar_instance;
} // namespace
// GENERATED_CODE_END
