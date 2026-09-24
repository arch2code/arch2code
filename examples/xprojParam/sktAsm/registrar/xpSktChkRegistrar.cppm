//

// GENERATED_CODE_PARAM --block=xpSktChk --parent=xpSktAsmTop/../../yaml/xpSktAsmTop.yaml
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module xpSktAsm.xpSktAsm_xpSktChk.registrar;
import xpSktAsm_xpSktChk.block;
import xpSktAsm.xpSktChk.config;

namespace {
struct _xpSktChk_registrar {
    _xpSktChk_registrar() {
        instanceFactory::registerBlock(
            "xpSktChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpSktChk<xpSktAsm_xpSktChkAsmConfig>>(blockName, variant, bbMode));
            },
            "asm", "xpSktAsm");
        instanceFactory::registerBlock(
            "xpSktChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpSktChk<xpSktAsm_xpSktChkAsmConfig>>(blockName, variant, bbMode));
            },
            "asm", "xpSktAsm.xpSktAsm_xpSktAsmTop.xpSktAsm_xpSktChk");
    }
};
static _xpSktChk_registrar _xpSktChk_registrar_instance;
} // namespace
// GENERATED_CODE_END
