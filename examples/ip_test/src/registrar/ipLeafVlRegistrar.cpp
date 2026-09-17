//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipLeaf --parent=src
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "ipLeaf_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VipLeaf_variantLeaf0_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "ipLeaf_variantLeaf0_hdl_sv_wrapper.h"
#else
#include "ipLeaf_variantLeaf0_hdl_sv_wrapper_xcelium.h"
#endif
import ip_test.ipLeaf.config;

namespace {
#if defined(VERILATOR)
using ipLeaf_variantLeaf0_hdl_sv_wrapper_dut_t = VipLeaf_variantLeaf0_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using ipLeaf_variantLeaf0_hdl_sv_wrapper_dut_t = ipLeaf_variantLeaf0_hdl_sv_wrapper;
#else
using ipLeaf_variantLeaf0_hdl_sv_wrapper_dut_t = ipLeaf_variantLeaf0_hdl_sv_wrapper;
#endif
struct _ipLeaf_vl_registrar {
    _ipLeaf_vl_registrar() {
        instanceFactory::registerBlock(
            "ipLeaf_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ipLeaf_hdl_sc_wrapper<ipLeaf_variantLeaf0_hdl_sv_wrapper_dut_t, ip_test_ipLeafVariantLeaf0Config>>(blockName, variant, bbMode));
            },
            "variantLeaf0", "ip_test");
        instanceFactory::registerBlock(
            "ipLeaf_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ipLeaf_hdl_sc_wrapper<ipLeaf_variantLeaf0_hdl_sv_wrapper_dut_t, ip_test_ipLeafVariantLeaf0Config>>(blockName, variant, bbMode));
            },
            "variantLeaf0", "ip_test.ip_test_src.ip_test_ipLeaf");
    }
};
static _ipLeaf_vl_registrar _ipLeaf_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
