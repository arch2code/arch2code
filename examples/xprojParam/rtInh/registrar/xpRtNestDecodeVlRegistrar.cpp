//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtNestDecode --parent=xpRtWrap/../../yaml/xpRtInh.yaml
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpRtNestDecode_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "Vp16_xpRtInh_xpRtWrap_c22_xpRtInh_xpRtNestDecode_use_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "p16_xpRtInh_xpRtWrap_c22_xpRtInh_xpRtNestDecode_use_hdl_sv_wrapper.h"
#else
#include "p16_xpRtInh_xpRtWrap_c22_xpRtInh_xpRtNestDecode_use_hdl_sv_wrapper_xcelium.h"
#endif
import xpRtInh.xpRtWrap.config;

namespace {
#if defined(VERILATOR)
using p16_xpRtInh_xpRtWrap_c22_xpRtInh_xpRtNestDecode_use_hdl_sv_wrapper_dut_t = Vp16_xpRtInh_xpRtWrap_c22_xpRtInh_xpRtNestDecode_use_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using p16_xpRtInh_xpRtWrap_c22_xpRtInh_xpRtNestDecode_use_hdl_sv_wrapper_dut_t = p16_xpRtInh_xpRtWrap_c22_xpRtInh_xpRtNestDecode_use_hdl_sv_wrapper;
#else
using p16_xpRtInh_xpRtWrap_c22_xpRtInh_xpRtNestDecode_use_hdl_sv_wrapper_dut_t = p16_xpRtInh_xpRtWrap_c22_xpRtInh_xpRtNestDecode_use_hdl_sv_wrapper;
#endif
struct _xpRtNestDecode_vl_registrar {
    _xpRtNestDecode_vl_registrar() {
        instanceFactory::registerBlock(
            "xpRtNestDecode_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpRtNestDecode_hdl_sc_wrapper<p16_xpRtInh_xpRtWrap_c22_xpRtInh_xpRtNestDecode_use_hdl_sv_wrapper_dut_t, xpRtInh_xpRtWrapUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpRtInh.xpRtInh_xpRtWrap.xpRtInh_xpRtNestDecode");
    }
};
static _xpRtNestDecode_vl_registrar _xpRtNestDecode_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
