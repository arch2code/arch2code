//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtWrap --parent=xpRtInhTop/../../yaml/xpRtInh.yaml
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpRtWrap_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VxpRtWrap_use_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "xpRtWrap_use_hdl_sv_wrapper.h"
#else
#include "xpRtWrap_use_hdl_sv_wrapper_xcelium.h"
#endif
import xpRtInh.xpRtWrap.config;

namespace {
#if defined(VERILATOR)
using xpRtWrap_use_hdl_sv_wrapper_dut_t = VxpRtWrap_use_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using xpRtWrap_use_hdl_sv_wrapper_dut_t = xpRtWrap_use_hdl_sv_wrapper;
#else
using xpRtWrap_use_hdl_sv_wrapper_dut_t = xpRtWrap_use_hdl_sv_wrapper;
#endif
struct _xpRtWrap_vl_registrar {
    _xpRtWrap_vl_registrar() {
        instanceFactory::registerBlock(
            "xpRtWrap_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpRtWrap_hdl_sc_wrapper<xpRtWrap_use_hdl_sv_wrapper_dut_t, xpRtInh_xpRtWrapUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpRtInh");
        instanceFactory::registerBlock(
            "xpRtWrap_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpRtWrap_hdl_sc_wrapper<xpRtWrap_use_hdl_sv_wrapper_dut_t, xpRtInh_xpRtWrapUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpRtInh.xpRtInh_xpRtInhTop.xpRtInh_xpRtWrap");
    }
};
static _xpRtWrap_vl_registrar _xpRtWrap_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
