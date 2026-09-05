//

// GENERATED_CODE_PARAM --block=xviTopSnk --parent=xviTop/../../yaml/xviTop.yaml
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xviLeafVariantConfig.h"

export module xviTop.xviTop_xviTopSnk.registrar;
import xviTop_xviTopSnk.block;
import xviTop.xviTopSnk.config;

namespace {
struct _xviTopSnk_registrar {
    _xviTopSnk_registrar() {
        instanceFactory::registerBlock(
            "xviTopSnk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviTopSnk<xviTop_xviTopSnkV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xviTop");
        instanceFactory::registerBlock(
            "xviTopSnk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviTopSnk<xviTop_xviTopSnkV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xviTop.xviTop.xviTop_xviTopSnk");
    }
};
static _xviTopSnk_registrar _xviTopSnk_registrar_instance;
} // namespace
// GENERATED_CODE_END
