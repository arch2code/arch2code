//

// GENERATED_CODE_PARAM --block=xpCppLeafNest --parent=xpCppWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module xpCppAxis.xpCppLeaf_xpCppLeafNest.registrar;
import xpCppLeaf_xpCppLeafNest.block;
import xpCppAxis.xpCppLeafNest.config;

namespace {
struct _xpCppLeafNest_registrar {
    _xpCppLeafNest_registrar() {
        instanceFactory::registerBlock(
            "xpCppLeafNest_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCppLeafNest<xpCppAxis_xpCppLeafNestV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpCppAxis.xpCppAxis_xpCppWrap.xpCppLeaf_xpCppLeafNest");
        instanceFactory::registerBlock(
            "xpCppLeafNest_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCppLeafNest<xpCppAxis_xpCppLeafNestV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpCppLeaf");
    }
};
static _xpCppLeafNest_registrar _xpCppLeafNest_registrar_instance;
} // namespace
// GENERATED_CODE_END
