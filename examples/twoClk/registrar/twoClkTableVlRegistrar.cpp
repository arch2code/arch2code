//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkTable --parent=twoClk
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "twoClkTable_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VtwoClkTable_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "twoClkTable_hdl_sv_wrapper.h"
#else
#include "twoClkTable_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using twoClkTable_hdl_sv_wrapper_dut_t = VtwoClkTable_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using twoClkTable_hdl_sv_wrapper_dut_t = twoClkTable_hdl_sv_wrapper;
#else
using twoClkTable_hdl_sv_wrapper_dut_t = twoClkTable_hdl_sv_wrapper;
#endif
struct _twoClkTable_vl_registrar {
    _twoClkTable_vl_registrar() {
        instanceFactory::registerBlock(
            "twoClkTable_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<twoClkTable_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "twoClk");
    }
};
static _twoClkTable_vl_registrar _twoClkTable_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
