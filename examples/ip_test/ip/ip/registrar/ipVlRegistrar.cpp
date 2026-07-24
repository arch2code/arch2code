//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip --parent=ipStdTop
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "ip_hdl_sc_wrapper.h"
#include "Vip_variant0_hdl_sv_wrapper.h"
#include "ipVariantConfig.h"

namespace {
struct _ip_vl_registrar {
    _ip_vl_registrar() {
        instanceFactory::registerBlock(
            "ip_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ip_hdl_sc_wrapper<Vip_variant0_hdl_sv_wrapper, ipVariant0Config>>(blockName, variant, bbMode));
            },
            "variant0", "ip");
    }
};
static _ip_vl_registrar _ip_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
