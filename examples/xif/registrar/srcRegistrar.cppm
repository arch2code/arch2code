//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=src --parent=xif_tb
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xifVariantConfig.h"

export module xif.xif_tb.src.registrar;
import xif_src.block;

namespace {
struct _src_registrar {
    _src_registrar() {
        instanceFactory::registerBlock(
            "src_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<src<srcSrcV0Config>>(blockName, variant, bbMode));
            },
            "srcV0", "xif");
    }
};
static _src_registrar _src_registrar_instance;
} // namespace
// GENERATED_CODE_END
