//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=blockRegistrar
#include "instanceFactory.h"
#include "blockBase.h"
#include "ip_topConfig.h"
#include "srcConfig.h"
#include "ipConfig.h"
#include "ip_top.h"

namespace {
struct _ip_top_registrar {
    _ip_top_registrar() {
        instanceFactory::registerBlock(
            "ip_top_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ip_top>(blockName, variant, bbMode));
            },
            "");
    }
};
static _ip_top_registrar _ip_top_registrar_instance;
} // namespace
// GENERATED_CODE_END
