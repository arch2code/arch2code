//

// GENERATED_CODE_PARAM --block=xpCstChkInc --parent=xpCstBindWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module xpCstBind.xpCstBind_xpCstChkInc.registrar;
import xpCstBind_xpCstChkInc.block;
import xpCstBind.xpCstChkInc.config;

namespace {
struct _xpCstChkInc_registrar {
    _xpCstChkInc_registrar() {
        instanceFactory::registerBlock(
            "xpCstChkInc_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstChkInc<xpCstBind_xpCstChkIncDfltConfig>>(blockName, variant, bbMode));
            },
            "dflt", "xpCstBind");
        instanceFactory::registerBlock(
            "xpCstChkInc_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpCstChkInc<xpCstBind_xpCstChkIncDfltConfig>>(blockName, variant, bbMode));
            },
            "dflt", "xpCstBind.xpCstBind_xpCstBindWrap.xpCstBind_xpCstChkInc");
    }
};
static _xpCstChkInc_registrar _xpCstChkInc_registrar_instance;
} // namespace
// GENERATED_CODE_END
