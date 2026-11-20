//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseLeaf --parent=uvmReuseLeaf_tb/../../yaml/uvmReuseLeaf_tb.yaml
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module uvmReuseLeaf.uvmReuseLeaf.registrar;
import uvmReuseLeaf.block;
import uvmReuseLeaf.config;

namespace {
struct _uvmReuseLeaf_registrar {
    _uvmReuseLeaf_registrar() {
        instanceFactory::registerBlock(
            "uvmReuseLeaf_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseLeaf<uvmReuseLeafW4Config>>(blockName, variant, bbMode));
            },
            "w4", "uvmReuseLeaf");
        instanceFactory::registerBlock(
            "uvmReuseLeaf_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseLeaf<uvmReuseLeafW4Config>>(blockName, variant, bbMode));
            },
            "w4", "uvmReuseLeaf.uvmReuseLeaf_tb.uvmReuseLeaf");
    }
};
static _uvmReuseLeaf_registrar _uvmReuseLeaf_registrar_instance;
} // namespace
// GENERATED_CODE_END
