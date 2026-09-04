//

// GENERATED_CODE_PARAM --block=xpDpTbPeer --parent=xpDpTop_tb
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpDpLeafVariantConfig.h"

export module xpDpTop.xpDpTop_xpDpTbPeer.registrar;
import xpDpTop_xpDpTbPeer.block;
import xpDpTop.xpDpTbPeer.config;

namespace {
struct _xpDpTbPeer_registrar {
    _xpDpTbPeer_registrar() {
        instanceFactory::registerBlock(
            "xpDpTbPeer_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpTbPeer<xpDpTop_xpDpTbPeerPeerConfig>>(blockName, variant, bbMode));
            },
            "peer", "xpDpTop");
        instanceFactory::registerBlock(
            "xpDpTbPeer_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpTbPeer<xpDpTop_xpDpTbPeerPeerConfig>>(blockName, variant, bbMode));
            },
            "peer", "xpDpTop.xpDpTop_tb.xpDpTop_xpDpTbPeer");
        instanceFactory::registerBlock(
            "xpDpTbPeer_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpTbPeer<xpDpTop_xpDpTbPeerPeer2Config>>(blockName, variant, bbMode));
            },
            "peer2", "xpDpTop");
        instanceFactory::registerBlock(
            "xpDpTbPeer_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpTbPeer<xpDpTop_xpDpTbPeerPeer2Config>>(blockName, variant, bbMode));
            },
            "peer2", "xpDpTop.xpDpTop_tb.xpDpTop_xpDpTbPeer");
    }
};
static _xpDpTbPeer_registrar _xpDpTbPeer_registrar_instance;
} // namespace
// GENERATED_CODE_END
