//

// GENERATED_CODE_PARAM --block=xpSktLeaf --parent=xpSktAsmTop/../../yaml/xpSktAsmTop.yaml
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module xpSktAsm.xpSktIp_xpSktLeaf.registrar;
import xpSktIp_xpSktLeaf.block;
import xpSktIp_xpSktLeaf.socket;
import xpSktAsm.xpSktLeaf.config;

namespace {
struct _xpSktLeaf_registrar {
    _xpSktLeaf_registrar() {
        instanceFactory::registerBlock(
            "xpSktLeaf_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpSktLeaf<xpSktAsm_xpSktLeafAsmConfig>>(blockName, variant, bbMode));
            },
            "asm", "xpSktAsm.xpSktAsm_xpSktAsmTop.xpSktIp_xpSktLeaf");
        instanceFactory::registerBlock(
            "xpSktLeaf_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpSktLeaf<xpSktAsm_xpSktLeafAsmConfig>>(blockName, variant, bbMode));
            },
            "asm", "xpSktIp");
        instanceFactory::registerBlock(
            "xpSktLeaf_socket",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpSktLeafSocket<xpSktAsm_xpSktLeafAsmConfig>>(blockName, variant, bbMode));
            },
            "asm", "xpSktAsm.xpSktAsm_xpSktAsmTop.xpSktIp_xpSktLeaf");
        instanceFactory::registerBlock(
            "xpSktLeaf_socket",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpSktLeafSocket<xpSktAsm_xpSktLeafAsmConfig>>(blockName, variant, bbMode));
            },
            "asm", "xpSktIp");
    }
};
static _xpSktLeaf_registrar _xpSktLeaf_registrar_instance;
} // namespace
// GENERATED_CODE_END
