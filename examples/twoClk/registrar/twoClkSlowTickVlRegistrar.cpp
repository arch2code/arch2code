//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkSlowTick --parent=twoClk
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "twoClkSlowTick_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VtwoClkSlowTick_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "twoClkSlowTick_hdl_sv_wrapper.h"
#else
#include "twoClkSlowTick_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using twoClkSlowTick_hdl_sv_wrapper_dut_t = VtwoClkSlowTick_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using twoClkSlowTick_hdl_sv_wrapper_dut_t = twoClkSlowTick_hdl_sv_wrapper;
#else
using twoClkSlowTick_hdl_sv_wrapper_dut_t = twoClkSlowTick_hdl_sv_wrapper;
#endif
struct _twoClkSlowTick_vl_registrar {
    _twoClkSlowTick_vl_registrar() {
        instanceFactory::registerBlock(
            "twoClkSlowTick_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<twoClkSlowTick_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "twoClk");
    }
};
static _twoClkSlowTick_vl_registrar _twoClkSlowTick_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
