//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip --parent=simple_ip
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "ip_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "Vip_variant0_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "ip_variant0_hdl_sv_wrapper.h"
#else
#include "ip_variant0_hdl_sv_wrapper_xcelium.h"
#endif
import ip.ip.config;

namespace {
#if defined(VERILATOR)
using ip_variant0_hdl_sv_wrapper_dut_t = Vip_variant0_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using ip_variant0_hdl_sv_wrapper_dut_t = ip_variant0_hdl_sv_wrapper;
#else
using ip_variant0_hdl_sv_wrapper_dut_t = ip_variant0_hdl_sv_wrapper;
#endif
static_assert(ipDataSt<ip_ipVariant0Config>::_bitWidth == 9, "ip_variant0_hdl_sv_wrapper: ipDataIf_data width differs from the generated boundary");
struct _ip_vl_registrar {
    _ip_vl_registrar() {
        instanceFactory::registerBlock(
            "ip_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ip_hdl_sc_wrapper<ip_variant0_hdl_sv_wrapper_dut_t, ip_ipVariant0Config>>(blockName, variant, bbMode));
            },
            "variant0", "ip");
        instanceFactory::registerBlock(
            "ip_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ip_hdl_sc_wrapper<ip_variant0_hdl_sv_wrapper_dut_t, ip_ipVariant0Config>>(blockName, variant, bbMode));
            },
            "variant0", "simple_ip.simple_ip.ip");
    }
};
static _ip_vl_registrar _ip_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
