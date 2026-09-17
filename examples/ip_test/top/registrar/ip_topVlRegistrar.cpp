//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip_top --parent=ip_top_tb
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "ip_top_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "Vip_top_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "ip_top_hdl_sv_wrapper.h"
#else
#include "ip_top_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using ip_top_hdl_sv_wrapper_dut_t = Vip_top_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using ip_top_hdl_sv_wrapper_dut_t = ip_top_hdl_sv_wrapper;
#else
using ip_top_hdl_sv_wrapper_dut_t = ip_top_hdl_sv_wrapper;
#endif
struct _ip_top_vl_registrar {
    _ip_top_vl_registrar() {
        instanceFactory::registerBlock(
            "ip_top_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ip_top_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "ip_test");
        instanceFactory::registerBlock(
            "ip_top_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ip_top_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "ip_test");
    }
};
static _ip_top_vl_registrar _ip_top_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
