//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip --parent=ipBridge
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module ipBridge.ip.registrar;
import ip.block;
import ip.ip.config;
import ipBridge.ip.config;

namespace {
struct _ip_registrar {
    _ip_registrar() {
        instanceFactory::registerBlock(
            "ip_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ip<ip_ipVariant0Config>>(blockName, variant, bbMode));
            },
            "variant0", "ip");
        instanceFactory::registerBlock(
            "ip_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ip<ip_ipVariant0Config>>(blockName, variant, bbMode));
            },
            "variant0", "ipBridge.ipBridge.ip");
        instanceFactory::registerBlock(
            "ip_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ip<ipBridge_ipVariant1Config>>(blockName, variant, bbMode));
            },
            "variant1", "ip");
        instanceFactory::registerBlock(
            "ip_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ip<ipBridge_ipVariant1Config>>(blockName, variant, bbMode));
            },
            "variant1", "ipBridge.ipBridge.ip");
    }
};
static _ip_registrar _ip_registrar_instance;
} // namespace
// GENERATED_CODE_END
