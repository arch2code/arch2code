//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipLeaf
// GENERATED_CODE_BEGIN --template=blockRegistrar
#include "instanceFactory.h"
#include "blockBase.h"
#include "ipLeafConfig.h"
#include "ipLeaf.h"

namespace {
struct _ipLeaf_registrar {
    _ipLeaf_registrar() {
        instanceFactory::registerBlock(
            "ipLeaf_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ipLeaf<ipLeafVariantLeaf0Config>>(blockName, variant, bbMode));
            },
            "variantLeaf0");
    }
};
static _ipLeaf_registrar _ipLeaf_registrar_instance;
} // namespace
// GENERATED_CODE_END
