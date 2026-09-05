//

// GENERATED_CODE_PARAM --block=xviLeaf --parent=xviTop/../../yaml/xviTop.yaml
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xviLeafVariantConfig.h"

export module xviTop.xviLeaf.registrar;
import xviLeaf.block;
import xviTop.xviLeaf.config;

namespace {
struct _xviLeaf_registrar {
    _xviLeaf_registrar() {
        instanceFactory::registerBlock(
            "xviLeaf_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviLeaf<xviTop_xviLeafV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xviLeaf");
        instanceFactory::registerBlock(
            "xviLeaf_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviLeaf<xviTop_xviLeafV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xviTop.xviTop.xviLeaf");
        instanceFactory::registerBlock(
            "xviLeaf_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviLeaf<xviTop_xviLeafVTopConfig>>(blockName, variant, bbMode));
            },
            "vTop", "xviLeaf");
        instanceFactory::registerBlock(
            "xviLeaf_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviLeaf<xviTop_xviLeafVTopConfig>>(blockName, variant, bbMode));
            },
            "vTop", "xviTop.xviTop.xviLeaf");
    }
};
static _xviLeaf_registrar _xviLeaf_registrar_instance;
} // namespace
// GENERATED_CODE_END
