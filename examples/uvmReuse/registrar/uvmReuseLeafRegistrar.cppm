//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseLeaf --parent=uvmReuseChain/../../yaml/uvmReuse.yaml
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module uvmReuse.uvmReuseLeaf.registrar;
import uvmReuseLeaf.block;
import uvmReuseLeaf.config;

namespace {
struct _uvmReuseLeaf_registrar {
    _uvmReuseLeaf_registrar() {
        instanceFactory::registerBlock(
            "uvmReuseLeaf_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseLeaf<uvmReuseLeafW8Config>>(blockName, variant, bbMode));
            },
            "w8", "uvmReuse.uvmReuse_uvmReuseChain.uvmReuseLeaf");
        instanceFactory::registerBlock(
            "uvmReuseLeaf_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseLeaf<uvmReuseLeafW8Config>>(blockName, variant, bbMode));
            },
            "w8", "uvmReuseLeaf");
    }
};
static _uvmReuseLeaf_registrar _uvmReuseLeaf_registrar_instance;
} // namespace
// GENERATED_CODE_END
