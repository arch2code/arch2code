//

// GENERATED_CODE_PARAM --block=xpCppLeafSign --parent=xpCppWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpCppWrapVariantConfig.h"

export module xpCppAxis.xpCppLeaf_xpCppLeafSign.registrar;
import xpCppLeaf_xpCppLeafSign.block;

namespace {
struct _xpCppLeafSign_registrar {
    _xpCppLeafSign_registrar() {
        instanceFactory::registerBlock(
            "xpCppLeafSign_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCppLeafSign<xpCppLeafSignV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpCppAxis.xpCppAxis_xpCppWrap.xpCppLeaf_xpCppLeafSign");
        instanceFactory::registerBlock(
            "xpCppLeafSign_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCppLeafSign<xpCppLeafSignV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpCppLeaf");
    }
};
static _xpCppLeafSign_registrar _xpCppLeafSign_registrar_instance;
} // namespace
// GENERATED_CODE_END
