//

// GENERATED_CODE_PARAM --block=vliCont --parent=vliWrap/../../yaml/vliCont.yaml
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module vlInh.vlInh_vliCont.registrar;
import vlInh_vliCont.block;
import vlInh.vliCont.config;

namespace {
struct _vliCont_registrar {
    _vliCont_registrar() {
        instanceFactory::registerBlock(
            "vliCont_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliCont<vlInh_vliContAltConfig>>(blockName, variant, bbMode));
            },
            "alt", "vlInh");
        instanceFactory::registerBlock(
            "vliCont_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliCont<vlInh_vliContAltConfig>>(blockName, variant, bbMode));
            },
            "alt", "vlInh.vlInh_vliWrap.vlInh_vliCont");
        instanceFactory::registerBlock(
            "vliCont_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliCont<vlInh_vliContDefaultConfig>>(blockName, variant, bbMode));
            },
            "default", "vlInh");
        instanceFactory::registerBlock(
            "vliCont_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliCont<vlInh_vliContDefaultConfig>>(blockName, variant, bbMode));
            },
            "default", "vlInh.vlInh_vliWrap.vlInh_vliCont");
    }
};
static _vliCont_registrar _vliCont_registrar_instance;
} // namespace
// GENERATED_CODE_END
