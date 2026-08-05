//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipBridge --parent=ip_top
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "ipBridge_hdl_sc_wrapper.h"
#include "VipBridge_hdl_sv_wrapper.h"
#include "ipVariantConfig.h"

namespace {
struct _ipBridge_vl_registrar {
    _ipBridge_vl_registrar() {
        instanceFactory::registerBlock(
            "ipBridge_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ipBridge_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "ipBridge");
    }
};
static _ipBridge_vl_registrar _ipBridge_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
