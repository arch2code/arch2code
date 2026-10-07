//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClk --parent=twoClk_tb
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "twoClk_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VtwoClk_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "twoClk_hdl_sv_wrapper.h"
#else
#include "twoClk_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using twoClk_hdl_sv_wrapper_dut_t = VtwoClk_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using twoClk_hdl_sv_wrapper_dut_t = twoClk_hdl_sv_wrapper;
#else
using twoClk_hdl_sv_wrapper_dut_t = twoClk_hdl_sv_wrapper;
#endif
struct _twoClk_vl_registrar {
    _twoClk_vl_registrar() {
        instanceFactory::registerBlock(
            "twoClk_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<twoClk_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "twoClk");
    }
};
static _twoClk_vl_registrar _twoClk_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
