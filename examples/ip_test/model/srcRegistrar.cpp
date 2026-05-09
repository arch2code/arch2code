//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=src
// GENERATED_CODE_BEGIN --template=blockRegistrar
#include "instanceFactory.h"
#include "blockBase.h"
#include "ipConfig.h"
#include "src.h"

namespace {
struct _src_registrar {
    _src_registrar() {
        instanceFactory::registerBlock(
            "src_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<src<ipDefaultConfig>>(blockName, variant, bbMode));
            },
            "");
    }
};
static _src_registrar _src_registrar_instance;
} // namespace
// GENERATED_CODE_END
