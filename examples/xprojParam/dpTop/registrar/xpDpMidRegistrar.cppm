//

// GENERATED_CODE_PARAM --block=xpDpMid --parent=xpDpWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpDpLeafVariantConfig.h"

export module xpDpTop.xpDpMid.registrar;
import xpDpMid.block;
import xpDpTop.xpDpMid.config;

namespace {
struct _xpDpMid_registrar {
    _xpDpMid_registrar() {
        instanceFactory::registerBlock(
            "xpDpMid_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpMid<xpDpTop_xpDpMidCustomer2Config>>(blockName, variant, bbMode));
            },
            "customer2", "xpDpMid");
        instanceFactory::registerBlock(
            "xpDpMid_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpMid<xpDpTop_xpDpMidCustomer2Config>>(blockName, variant, bbMode));
            },
            "customer2", "xpDpTop.xpDpTop_xpDpWrap.xpDpMid");
        instanceFactory::registerBlock(
            "xpDpMid_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpMid<xpDpTop_xpDpMidCustomer3Config>>(blockName, variant, bbMode));
            },
            "customer3", "xpDpMid");
        instanceFactory::registerBlock(
            "xpDpMid_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpMid<xpDpTop_xpDpMidCustomer3Config>>(blockName, variant, bbMode));
            },
            "customer3", "xpDpTop.xpDpTop_xpDpWrap.xpDpMid");
    }
};
static _xpDpMid_registrar _xpDpMid_registrar_instance;
} // namespace
// GENERATED_CODE_END
