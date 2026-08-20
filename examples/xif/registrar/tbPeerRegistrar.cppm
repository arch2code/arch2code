//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=tbPeer --parent=xif_tb
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xifVariantConfig.h"

export module xif.xif_tb.tbPeer.registrar;
import xif_tbPeer.block;

namespace {
struct _tbPeer_registrar {
    _tbPeer_registrar() {
        instanceFactory::registerBlock(
            "tbPeer_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<tbPeer<tbPeerPv0Config>>(blockName, variant, bbMode));
            },
            "pv0", "xif");
    }
};
static _tbPeer_registrar _tbPeer_registrar_instance;
} // namespace
// GENERATED_CODE_END
