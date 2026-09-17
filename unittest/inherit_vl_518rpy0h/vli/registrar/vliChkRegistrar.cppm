//

// GENERATED_CODE_PARAM --block=vliChk --parent=vliWrap/../../yaml/vliCont.yaml
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module vlInh.vlInh_vliChk.registrar;
import vlInh_vliChk.block;
import vlInh.vliChk.config;

namespace {
struct _vliChk_registrar {
    _vliChk_registrar() {
        instanceFactory::registerBlock(
            "vliChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliChk<vlInh_vliChkChkAltConfig>>(blockName, variant, bbMode));
            },
            "chkAlt", "vlInh");
        instanceFactory::registerBlock(
            "vliChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliChk<vlInh_vliChkChkAltConfig>>(blockName, variant, bbMode));
            },
            "chkAlt", "vlInh.vlInh_vliWrap.vlInh_vliChk");
        instanceFactory::registerBlock(
            "vliChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliChk<vlInh_vliChkChkDefConfig>>(blockName, variant, bbMode));
            },
            "chkDef", "vlInh");
        instanceFactory::registerBlock(
            "vliChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliChk<vlInh_vliChkChkDefConfig>>(blockName, variant, bbMode));
            },
            "chkDef", "vlInh.vlInh_vliWrap.vlInh_vliChk");
        instanceFactory::registerBlock(
            "vliChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliChk<vlInh_vliChkChkSoloConfig>>(blockName, variant, bbMode));
            },
            "chkSolo", "vlInh");
        instanceFactory::registerBlock(
            "vliChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliChk<vlInh_vliChkChkSoloConfig>>(blockName, variant, bbMode));
            },
            "chkSolo", "vlInh.vlInh_vliWrap.vlInh_vliChk");
    }
};
static _vliChk_registrar _vliChk_registrar_instance;
} // namespace
// GENERATED_CODE_END
