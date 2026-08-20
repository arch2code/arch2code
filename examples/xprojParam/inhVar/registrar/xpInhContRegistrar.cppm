//

// GENERATED_CODE_PARAM --block=xpInhCont --parent=xpInhWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpInhContVariantConfig.h"

export module xpInhVar.xpInhWrap.xpInhCont.registrar;
import xpInhVar_xpInhCont.block;

namespace {
struct _xpInhCont_registrar {
    _xpInhCont_registrar() {
        instanceFactory::registerBlock(
            "xpInhCont_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpInhCont<xpInhContAltConfig>>(blockName, variant, bbMode));
            },
            "alt", "xpInhVar");
        instanceFactory::registerBlock(
            "xpInhCont_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpInhCont<xpInhContDefaultConfig>>(blockName, variant, bbMode));
            },
            "default", "xpInhVar");
    }
};
static _xpInhCont_registrar _xpInhCont_registrar_instance;
} // namespace
// GENERATED_CODE_END
