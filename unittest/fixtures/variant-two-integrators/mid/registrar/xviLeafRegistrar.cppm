//

// GENERATED_CODE_PARAM --block=xviLeaf --parent=xviMid/../../yaml/xviMid.yaml
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xviLeafVariantConfig.h"

export module xviMid.xviLeaf.registrar;
import xviLeaf.block;
import xviMid.xviLeaf.config;

namespace {
struct _xviLeaf_registrar {
    _xviLeaf_registrar() {
        instanceFactory::registerBlock(
            "xviLeaf_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviLeaf<xviMid_xviLeafV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xviLeaf");
        instanceFactory::registerBlock(
            "xviLeaf_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviLeaf<xviMid_xviLeafV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xviMid.xviMid.xviLeaf");
        instanceFactory::registerBlock(
            "xviLeaf_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviLeaf<xviMid_xviLeafVMidConfig>>(blockName, variant, bbMode));
            },
            "vMid", "xviLeaf");
        instanceFactory::registerBlock(
            "xviLeaf_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviLeaf<xviMid_xviLeafVMidConfig>>(blockName, variant, bbMode));
            },
            "vMid", "xviMid.xviMid.xviLeaf");
    }
};
static _xviLeaf_registrar _xviLeaf_registrar_instance;
} // namespace
// GENERATED_CODE_END
