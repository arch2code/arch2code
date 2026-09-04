//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=sink --parent=xif_tb
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xifVariantConfig.h"

export module xif.xif_sink.registrar;
import xif_sink.block;

namespace {
struct _sink_registrar {
    _sink_registrar() {
        instanceFactory::registerBlock(
            "sink_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<sink<sinkSinkV0Config>>(blockName, variant, bbMode));
            },
            "sinkV0", "xif");
        instanceFactory::registerBlock(
            "sink_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<sink<sinkSinkV0Config>>(blockName, variant, bbMode));
            },
            "sinkV0", "xif.xif_tb.xif_sink");
    }
};
static _sink_registrar _sink_registrar_instance;
} // namespace
// GENERATED_CODE_END
