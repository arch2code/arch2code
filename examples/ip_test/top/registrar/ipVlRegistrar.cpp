//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip --parent=ip_top
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "ip_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "Vip_variant0_hdl_sv_wrapper.h"
#include "VipBridge_ip_variant1_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "ip_variant0_hdl_sv_wrapper.h"
#include "ipBridge_ip_variant1_hdl_sv_wrapper.h"
#else
#include "ip_variant0_hdl_sv_wrapper_xcelium.h"
#include "ipBridge_ip_variant1_hdl_sv_wrapper_xcelium.h"
#endif
import ip.ip.config;
import ipBridge.ip.config;

namespace {
#if defined(VERILATOR)
using ip_variant0_hdl_sv_wrapper_dut_t = Vip_variant0_hdl_sv_wrapper;
using ipBridge_ip_variant1_hdl_sv_wrapper_dut_t = VipBridge_ip_variant1_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using ip_variant0_hdl_sv_wrapper_dut_t = ip_variant0_hdl_sv_wrapper;
using ipBridge_ip_variant1_hdl_sv_wrapper_dut_t = ipBridge_ip_variant1_hdl_sv_wrapper;
#else
using ip_variant0_hdl_sv_wrapper_dut_t = ip_variant0_hdl_sv_wrapper;
using ipBridge_ip_variant1_hdl_sv_wrapper_dut_t = ipBridge_ip_variant1_hdl_sv_wrapper;
#endif
static_assert(ipDataSt<ip_ipVariant0Config>::_bitWidth == 9, "ip_variant0_hdl_sv_wrapper: ipDataIf_data width differs from the generated boundary");
static_assert(ipDataSt<ipBridge_ipVariant1Config>::_bitWidth == 71, "ipBridge_ip_variant1_hdl_sv_wrapper: ipDataIf_data width differs from the generated boundary");
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
            "variant0", "ip_test.ip_test_ip_top.ip");
        instanceFactory::registerBlock(
            "ip_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ip_hdl_sc_wrapper<ipBridge_ip_variant1_hdl_sv_wrapper_dut_t, ipBridge_ipVariant1Config>>(blockName, variant, bbMode));
            },
            "variant1", "ip");
        instanceFactory::registerBlock(
            "ip_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ip_hdl_sc_wrapper<ipBridge_ip_variant1_hdl_sv_wrapper_dut_t, ipBridge_ipVariant1Config>>(blockName, variant, bbMode));
            },
            "variant1", "ip_test.ip_test_ip_top.ip");
    }
};
static _ip_vl_registrar _ip_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
