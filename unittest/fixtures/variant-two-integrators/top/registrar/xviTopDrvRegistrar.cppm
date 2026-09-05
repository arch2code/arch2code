//

// GENERATED_CODE_PARAM --block=xviTopDrv --parent=xviTop/../../yaml/xviTop.yaml
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xviLeafVariantConfig.h"

export module xviTop.xviTop_xviTopDrv.registrar;
import xviTop_xviTopDrv.block;
import xviTop.xviTopDrv.config;

namespace {
struct _xviTopDrv_registrar {
    _xviTopDrv_registrar() {
        instanceFactory::registerBlock(
            "xviTopDrv_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviTopDrv<xviTop_xviTopDrvV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xviTop");
        instanceFactory::registerBlock(
            "xviTopDrv_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviTopDrv<xviTop_xviTopDrvV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xviTop.xviTop.xviTop_xviTopDrv");
    }
};
static _xviTopDrv_registrar _xviTopDrv_registrar_instance;
} // namespace
// GENERATED_CODE_END
