//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip --parent=ipStdTop
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module ip.ip.registrar;
import ip.block;
import ip.ip.config;

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
            "variant0", "ip.ip_ipStdTop.ip");
    }
};
static _ip_registrar _ip_registrar_instance;
} // namespace
// GENERATED_CODE_END
