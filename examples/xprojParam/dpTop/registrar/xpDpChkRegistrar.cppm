//

// GENERATED_CODE_PARAM --block=xpDpChk --parent=xpDpWrap
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpDpLeafVariantConfig.h"

export module xpDpTop.xpDpTop_xpDpChk.registrar;
import xpDpTop_xpDpChk.block;
import xpDpTop.xpDpChk.config;

namespace {
struct _xpDpChk_registrar {
    _xpDpChk_registrar() {
        instanceFactory::registerBlock(
            "xpDpChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpChk<xpDpTop_xpDpChkCustomerConfig>>(blockName, variant, bbMode));
            },
            "customer", "xpDpTop");
        instanceFactory::registerBlock(
            "xpDpChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpChk<xpDpTop_xpDpChkCustomerConfig>>(blockName, variant, bbMode));
            },
            "customer", "xpDpTop.xpDpTop_xpDpWrap.xpDpTop_xpDpChk");
        instanceFactory::registerBlock(
            "xpDpChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpChk<xpDpTop_xpDpChkCustomer2Config>>(blockName, variant, bbMode));
            },
            "customer2", "xpDpTop");
        instanceFactory::registerBlock(
            "xpDpChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpChk<xpDpTop_xpDpChkCustomer2Config>>(blockName, variant, bbMode));
            },
            "customer2", "xpDpTop.xpDpTop_xpDpWrap.xpDpTop_xpDpChk");
        instanceFactory::registerBlock(
            "xpDpChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpChk<xpDpTop_xpDpChkCustomer3Config>>(blockName, variant, bbMode));
            },
            "customer3", "xpDpTop");
        instanceFactory::registerBlock(
            "xpDpChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpChk<xpDpTop_xpDpChkCustomer3Config>>(blockName, variant, bbMode));
            },
            "customer3", "xpDpTop.xpDpTop_xpDpWrap.xpDpTop_xpDpChk");
        instanceFactory::registerBlock(
            "xpDpChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpChk<xpDpTop_xpDpChkLeafXConfig>>(blockName, variant, bbMode));
            },
            "leafX", "xpDpTop");
        instanceFactory::registerBlock(
            "xpDpChk_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpDpChk<xpDpTop_xpDpChkLeafXConfig>>(blockName, variant, bbMode));
            },
            "leafX", "xpDpTop.xpDpTop_xpDpWrap.xpDpTop_xpDpChk");
    }
};
static _xpDpChk_registrar _xpDpChk_registrar_instance;
} // namespace
// GENERATED_CODE_END
