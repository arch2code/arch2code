//

// GENERATED_CODE_PARAM --block=xpDpLeaf --parent=xpDpWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpDpLeafVariantConfig.h"

export module xpDpTop.xpDpLeaf.registrar;
import xpDpLeaf.block;

namespace {
struct _xpDpLeaf_registrar {
    _xpDpLeaf_registrar() {
        instanceFactory::registerBlock(
            "xpDpLeaf_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpLeaf<xpDpLeafDefaultConfig>>(blockName, variant, bbMode));
            },
            "customer", "xpDpLeaf");
        instanceFactory::registerBlock(
            "xpDpLeaf_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpLeaf<xpDpLeafDefaultConfig>>(blockName, variant, bbMode));
            },
            "customer", "xpDpTop.xpDpTop_xpDpWrap.xpDpLeaf");
    }
};
static _xpDpLeaf_registrar _xpDpLeaf_registrar_instance;
} // namespace
// GENERATED_CODE_END
