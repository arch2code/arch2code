//

// GENERATED_CODE_PARAM --block=vliLeaf --parent=vliWrap/../../yaml/vliCont.yaml
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module vlInh.vlInh_vliLeaf.registrar;
import vlInh_vliLeaf.block;
import vlInh.vliLeaf.config;

namespace {
struct _vliLeaf_registrar {
    _vliLeaf_registrar() {
        instanceFactory::registerBlock(
            "vliLeaf_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliLeaf<vlInh_vliLeafSoloConfig>>(blockName, variant, bbMode));
            },
            "solo", "vlInh");
        instanceFactory::registerBlock(
            "vliLeaf_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliLeaf<vlInh_vliLeafSoloConfig>>(blockName, variant, bbMode));
            },
            "solo", "vlInh.vlInh_vliCont.vlInh_vliLeaf");
        instanceFactory::registerBlock(
            "vliLeaf_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliLeaf<vlInh_vliLeafSoloConfig>>(blockName, variant, bbMode));
            },
            "solo", "vlInh.vlInh_vliWrap.vlInh_vliLeaf");
    }
};
static _vliLeaf_registrar _vliLeaf_registrar_instance;
} // namespace
// GENERATED_CODE_END
