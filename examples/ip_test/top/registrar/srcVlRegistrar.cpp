//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=src --parent=ip_top
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "src_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "Vsrc_variantSrc0_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "src_variantSrc0_hdl_sv_wrapper.h"
#else
#include "src_variantSrc0_hdl_sv_wrapper_xcelium.h"
#endif
import ip_test.src.config;

namespace {
#if defined(VERILATOR)
using src_variantSrc0_hdl_sv_wrapper_dut_t = Vsrc_variantSrc0_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using src_variantSrc0_hdl_sv_wrapper_dut_t = src_variantSrc0_hdl_sv_wrapper;
#else
using src_variantSrc0_hdl_sv_wrapper_dut_t = src_variantSrc0_hdl_sv_wrapper;
#endif
static_assert(srcOut0St<ip_test_srcVariantSrc0Config>::_bitWidth == 9, "src_variantSrc0_hdl_sv_wrapper: out0_data width differs from the generated boundary");
static_assert(srcOut1St<ip_test_srcVariantSrc0Config>::_bitWidth == 71, "src_variantSrc0_hdl_sv_wrapper: out1_data width differs from the generated boundary");
static_assert(srcOut0St<ip_test_srcVariantSrc0Config>::_bitWidth == 9, "src_variantSrc0_hdl_sv_wrapper: out2_data width differs from the generated boundary");
static_assert(srcOut1St<ip_test_srcVariantSrc0Config>::_bitWidth == 71, "src_variantSrc0_hdl_sv_wrapper: out3_data width differs from the generated boundary");
struct _src_vl_registrar {
    _src_vl_registrar() {
        instanceFactory::registerBlock(
            "src_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<src_hdl_sc_wrapper<src_variantSrc0_hdl_sv_wrapper_dut_t, ip_test_srcVariantSrc0Config>>(blockName, variant, bbMode));
            },
            "variantSrc0", "ip_test");
        instanceFactory::registerBlock(
            "src_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<src_hdl_sc_wrapper<src_variantSrc0_hdl_sv_wrapper_dut_t, ip_test_srcVariantSrc0Config>>(blockName, variant, bbMode));
            },
            "variantSrc0", "ip_test.ip_test_ip_top.ip_test_src");
    }
};
static _src_vl_registrar _src_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
