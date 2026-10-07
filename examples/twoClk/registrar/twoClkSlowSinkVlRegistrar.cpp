//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkSlowSink --parent=twoClk
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "twoClkSlowSink_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VtwoClkSlowSink_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "twoClkSlowSink_hdl_sv_wrapper.h"
#else
#include "twoClkSlowSink_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using twoClkSlowSink_hdl_sv_wrapper_dut_t = VtwoClkSlowSink_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using twoClkSlowSink_hdl_sv_wrapper_dut_t = twoClkSlowSink_hdl_sv_wrapper;
#else
using twoClkSlowSink_hdl_sv_wrapper_dut_t = twoClkSlowSink_hdl_sv_wrapper;
#endif
struct _twoClkSlowSink_vl_registrar {
    _twoClkSlowSink_vl_registrar() {
        instanceFactory::registerBlock(
            "twoClkSlowSink_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<twoClkSlowSink_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "twoClk");
    }
};
static _twoClkSlowSink_vl_registrar _twoClkSlowSink_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
