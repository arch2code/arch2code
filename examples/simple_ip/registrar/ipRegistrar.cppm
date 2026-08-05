//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip --parent=simple_ip
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "ipVariantConfig.h"

export module simple_ip.simple_ip.ip.registrar;
import ip.block;

namespace {
struct _ip_registrar {
    _ip_registrar() {
        instanceFactory::registerBlock(
            "ip_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ip<ipVariant0Config>>(blockName, variant, bbMode));
            },
            "variant0", "simple_ip");
    }
};
static _ip_registrar _ip_registrar_instance;
} // namespace
// GENERATED_CODE_END
