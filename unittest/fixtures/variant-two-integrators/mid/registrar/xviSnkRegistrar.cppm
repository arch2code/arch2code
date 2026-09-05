//

// GENERATED_CODE_PARAM --block=xviSnk --parent=xviMid/../../yaml/xviMid.yaml
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xviLeafVariantConfig.h"

export module xviMid.xviMid_xviSnk.registrar;
import xviMid_xviSnk.block;
import xviMid.xviSnk.config;

namespace {
struct _xviSnk_registrar {
    _xviSnk_registrar() {
        instanceFactory::registerBlock(
            "xviSnk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviSnk<xviMid_xviSnkV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xviMid");
        instanceFactory::registerBlock(
            "xviSnk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviSnk<xviMid_xviSnkV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xviMid.xviMid.xviMid_xviSnk");
    }
};
static _xviSnk_registrar _xviSnk_registrar_instance;
} // namespace
// GENERATED_CODE_END
