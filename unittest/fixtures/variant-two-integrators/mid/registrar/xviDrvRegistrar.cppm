//

// GENERATED_CODE_PARAM --block=xviDrv --parent=xviMid/../../yaml/xviMid.yaml
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xviLeafVariantConfig.h"

export module xviMid.xviMid_xviDrv.registrar;
import xviMid_xviDrv.block;
import xviMid.xviDrv.config;

namespace {
struct _xviDrv_registrar {
    _xviDrv_registrar() {
        instanceFactory::registerBlock(
            "xviDrv_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviDrv<xviMid_xviDrvV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xviMid");
        instanceFactory::registerBlock(
            "xviDrv_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviDrv<xviMid_xviDrvV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xviMid.xviMid.xviMid_xviDrv");
    }
};
static _xviDrv_registrar _xviDrv_registrar_instance;
} // namespace
// GENERATED_CODE_END
