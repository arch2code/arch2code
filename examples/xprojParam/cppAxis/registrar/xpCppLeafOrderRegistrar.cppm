//

// GENERATED_CODE_PARAM --block=xpCppLeafOrder --parent=xpCppWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpCppWrapVariantConfig.h"

export module xpCppAxis.xpCppLeaf_xpCppLeafOrder.registrar;
import xpCppLeaf_xpCppLeafOrder.block;

namespace {
struct _xpCppLeafOrder_registrar {
    _xpCppLeafOrder_registrar() {
        instanceFactory::registerBlock(
            "xpCppLeafOrder_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCppLeafOrder<xpCppLeafOrderV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpCppAxis.xpCppAxis_xpCppWrap.xpCppLeaf_xpCppLeafOrder");
        instanceFactory::registerBlock(
            "xpCppLeafOrder_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCppLeafOrder<xpCppLeafOrderV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpCppLeaf");
    }
};
static _xpCppLeafOrder_registrar _xpCppLeafOrder_registrar_instance;
} // namespace
// GENERATED_CODE_END
