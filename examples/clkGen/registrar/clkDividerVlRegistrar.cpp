//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=clkDivider --parent=clkGen
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "clkDivider_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VclkDivider_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "clkDivider_hdl_sv_wrapper.h"
#else
#include "clkDivider_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using clkDivider_hdl_sv_wrapper_dut_t = VclkDivider_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using clkDivider_hdl_sv_wrapper_dut_t = clkDivider_hdl_sv_wrapper;
#else
using clkDivider_hdl_sv_wrapper_dut_t = clkDivider_hdl_sv_wrapper;
#endif
struct _clkDivider_vl_registrar {
    _clkDivider_vl_registrar() {
        instanceFactory::registerBlock(
            "clkDivider_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<clkDivider_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "clkGen");
    }
};
static _clkDivider_vl_registrar _clkDivider_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
