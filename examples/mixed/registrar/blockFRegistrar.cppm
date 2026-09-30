//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockF --parent=blockB
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module mixed.mixed_blockF.registrar;
import mixed_blockF.block;
import mixed.blockF.config;

namespace {
struct _blockF_registrar {
    _blockF_registrar() {
        instanceFactory::registerBlock(
            "blockF_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockF<mixed_blockFVariant0Config>>(blockName, variant, bbMode));
            },
            "variant0", "mixed");
        instanceFactory::registerBlock(
            "blockF_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockF<mixed_blockFVariant0Config>>(blockName, variant, bbMode));
            },
            "variant0", "mixed.mixed_blockB.mixed_blockF");
        instanceFactory::registerBlock(
            "blockF_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockF<mixed_blockFVariant1Config>>(blockName, variant, bbMode));
            },
            "variant1", "mixed");
        instanceFactory::registerBlock(
            "blockF_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockF<mixed_blockFVariant1Config>>(blockName, variant, bbMode));
            },
            "variant1", "mixed.mixed_blockB.mixed_blockF");
    }
};
static _blockF_registrar _blockF_registrar_instance;
} // namespace
// GENERATED_CODE_END
