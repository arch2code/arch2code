//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtInhTop --parent=xpRtInhTop_tb/../../yaml/xpRtInh.yaml
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpRtInhTop_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VxpRtInhTop_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "xpRtInhTop_hdl_sv_wrapper.h"
#else
#include "xpRtInhTop_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using xpRtInhTop_hdl_sv_wrapper_dut_t = VxpRtInhTop_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using xpRtInhTop_hdl_sv_wrapper_dut_t = xpRtInhTop_hdl_sv_wrapper;
#else
using xpRtInhTop_hdl_sv_wrapper_dut_t = xpRtInhTop_hdl_sv_wrapper;
#endif
struct _xpRtInhTop_vl_registrar {
    _xpRtInhTop_vl_registrar() {
        instanceFactory::registerBlock(
            "xpRtInhTop_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpRtInhTop_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "xpRtInh");
        instanceFactory::registerBlock(
            "xpRtInhTop_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpRtInhTop_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "xpRtInh");
    }
};
static _xpRtInhTop_vl_registrar _xpRtInhTop_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
