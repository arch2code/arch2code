//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipLeaf --parent=src
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "ipLeafVariantConfig.h"

export module ip_test.ip_test_ipLeaf.registrar;
import ip_test_ipLeaf.block;

namespace {
struct _ipLeaf_registrar {
    _ipLeaf_registrar() {
        instanceFactory::registerBlock(
            "ipLeaf_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ipLeaf<ipLeafVariantLeaf0Config>>(blockName, variant, bbMode));
            },
            "variantLeaf0", "ip_test");
        instanceFactory::registerBlock(
            "ipLeaf_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ipLeaf<ipLeafVariantLeaf0Config>>(blockName, variant, bbMode));
            },
            "variantLeaf0", "ip_test.ip_test_src.ip_test_ipLeaf");
    }
};
static _ipLeaf_registrar _ipLeaf_registrar_instance;
} // namespace
// GENERATED_CODE_END
