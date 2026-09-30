//

// GENERATED_CODE_PARAM --block=xpCstSharedChk --parent=xpCstSharedWrap/../../yaml/xpCstSharedTop.yaml
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module xpCstShared.xpCstShared_xpCstSharedChk.registrar;
import xpCstShared_xpCstSharedChk.block;
import xpCstShared.xpCstSharedChk.config;

namespace {
struct _xpCstSharedChk_registrar {
    _xpCstSharedChk_registrar() {
        instanceFactory::registerBlock(
            "xpCstSharedChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstSharedChk<xpCstShared_xpCstSharedChkUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpCstShared");
        instanceFactory::registerBlock(
            "xpCstSharedChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstSharedChk<xpCstShared_xpCstSharedChkUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpCstShared.xpCstShared_xpCstSharedWrap.xpCstShared_xpCstSharedChk");
    }
};
static _xpCstSharedChk_registrar _xpCstSharedChk_registrar_instance;
} // namespace
// GENERATED_CODE_END
