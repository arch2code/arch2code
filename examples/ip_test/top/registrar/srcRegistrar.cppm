//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=src --parent=ip_top
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "ipLeafVariantConfig.h"
#include "srcVariantConfig.h"

export module ip_test.ip_top.src.registrar;
import ip_test_src.block;

namespace {
struct _src_registrar {
    _src_registrar() {
        instanceFactory::registerBlock(
            "src_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<src<srcVariantSrc0Config>>(blockName, variant, bbMode));
            },
            "variantSrc0", "ip_test");
    }
};
static _src_registrar _src_registrar_instance;
} // namespace
// GENERATED_CODE_END
