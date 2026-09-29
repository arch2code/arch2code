//

// GENERATED_CODE_PARAM --block=xpCstChkOwn --parent=xpCstBindWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module xpCstBind.xpCstBind_xpCstChkOwn.registrar;
import xpCstBind_xpCstChkOwn.block;
import xpCstBind.xpCstChkOwn.config;

namespace {
struct _xpCstChkOwn_registrar {
    _xpCstChkOwn_registrar() {
        instanceFactory::registerBlock(
            "xpCstChkOwn_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstChkOwn<xpCstBind_xpCstChkOwnUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpCstBind");
        instanceFactory::registerBlock(
            "xpCstChkOwn_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstChkOwn<xpCstBind_xpCstChkOwnUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpCstBind.xpCstBind_xpCstBindWrap.xpCstBind_xpCstChkOwn");
    }
};
static _xpCstChkOwn_registrar _xpCstChkOwn_registrar_instance;
} // namespace
// GENERATED_CODE_END
