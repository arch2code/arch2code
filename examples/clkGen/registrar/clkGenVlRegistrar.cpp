//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=clkGen --parent=clkGen_tb
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "clkGen_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VclkGen_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "clkGen_hdl_sv_wrapper.h"
#else
#include "clkGen_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using clkGen_hdl_sv_wrapper_dut_t = VclkGen_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using clkGen_hdl_sv_wrapper_dut_t = clkGen_hdl_sv_wrapper;
#else
using clkGen_hdl_sv_wrapper_dut_t = clkGen_hdl_sv_wrapper;
#endif
struct _clkGen_vl_registrar {
    _clkGen_vl_registrar() {
        instanceFactory::registerBlock(
            "clkGen_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<clkGen_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "clkGen");
    }
};
static _clkGen_vl_registrar _clkGen_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
