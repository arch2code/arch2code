//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseChain --parent=uvmReuse_tb/../../yaml/uvmReuse.yaml
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module uvmReuse.uvmReuse_uvmReuseChain.registrar;
import uvmReuse_uvmReuseChain.block;
import uvmReuse.uvmReuseChain.config;

namespace {
struct _uvmReuseChain_registrar {
    _uvmReuseChain_registrar() {
        instanceFactory::registerBlock(
            "uvmReuseChain_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseChain<uvmReuse_uvmReuseChainV8Config>>(blockName, variant, bbMode));
            },
            "v8", "uvmReuse");
        instanceFactory::registerBlock(
            "uvmReuseChain_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseChain<uvmReuse_uvmReuseChainV8Config>>(blockName, variant, bbMode));
            },
            "v8", "uvmReuse.uvmReuse_tb.uvmReuse_uvmReuseChain");
    }
};
static _uvmReuseChain_registrar _uvmReuseChain_registrar_instance;
} // namespace
// GENERATED_CODE_END
