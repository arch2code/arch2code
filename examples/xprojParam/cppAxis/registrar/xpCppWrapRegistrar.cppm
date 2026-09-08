//

// GENERATED_CODE_PARAM --block=xpCppWrap --parent=xpCppAxisTop
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module xpCppAxis.xpCppAxis_xpCppWrap.registrar;
import xpCppAxis_xpCppWrap.block;
import xpCppAxis.xpCppWrap.config;

namespace {
struct _xpCppWrap_registrar {
    _xpCppWrap_registrar() {
        instanceFactory::registerBlock(
            "xpCppWrap_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCppWrap<xpCppAxis_xpCppWrapV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpCppAxis");
        instanceFactory::registerBlock(
            "xpCppWrap_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCppWrap<xpCppAxis_xpCppWrapV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xpCppAxis.xpCppAxis_xpCppAxisTop.xpCppAxis_xpCppWrap");
    }
};
static _xpCppWrap_registrar _xpCppWrap_registrar_instance;
} // namespace
// GENERATED_CODE_END
