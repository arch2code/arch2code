//

// GENERATED_CODE_PARAM --block=xpInhChk --parent=xpInhWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module xpInhVar.xpInhVar_xpInhChk.registrar;
import xpInhVar_xpInhChk.block;
import xpInhVar.xpInhChk.config;

namespace {
struct _xpInhChk_registrar {
    _xpInhChk_registrar() {
        instanceFactory::registerBlock(
            "xpInhChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpInhChk<xpInhVar_xpInhChkChkAltConfig>>(blockName, variant, bbMode));
            },
            "chkAlt", "xpInhVar");
        instanceFactory::registerBlock(
            "xpInhChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpInhChk<xpInhVar_xpInhChkChkAltConfig>>(blockName, variant, bbMode));
            },
            "chkAlt", "xpInhVar.xpInhVar_xpInhWrap.xpInhVar_xpInhChk");
        instanceFactory::registerBlock(
            "xpInhChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpInhChk<xpInhVar_xpInhChkChkDefConfig>>(blockName, variant, bbMode));
            },
            "chkDef", "xpInhVar");
        instanceFactory::registerBlock(
            "xpInhChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpInhChk<xpInhVar_xpInhChkChkDefConfig>>(blockName, variant, bbMode));
            },
            "chkDef", "xpInhVar.xpInhVar_xpInhWrap.xpInhVar_xpInhChk");
    }
};
static _xpInhChk_registrar _xpInhChk_registrar_instance;
} // namespace
// GENERATED_CODE_END
