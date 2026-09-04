//

// GENERATED_CODE_PARAM --block=xpCppLeafEq --parent=xpCppWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpCppWrapVariantConfig.h"

export module xpCppAxis.xpCppLeaf_xpCppLeafEq.registrar;
import xpCppLeaf_xpCppLeafEq.block;

namespace {
struct _xpCppLeafEq_registrar {
    _xpCppLeafEq_registrar() {
        instanceFactory::registerBlock(
            "xpCppLeafEq_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCppLeafEq<xpCppLeafEqV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpCppAxis.xpCppAxis_xpCppWrap.xpCppLeaf_xpCppLeafEq");
        instanceFactory::registerBlock(
            "xpCppLeafEq_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCppLeafEq<xpCppLeafEqV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpCppLeaf");
    }
};
static _xpCppLeafEq_registrar _xpCppLeafEq_registrar_instance;
} // namespace
// GENERATED_CODE_END
