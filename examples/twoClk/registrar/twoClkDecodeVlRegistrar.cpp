//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkDecode --parent=twoClk
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "twoClkDecode_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VtwoClkDecode_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "twoClkDecode_hdl_sv_wrapper.h"
#else
#include "twoClkDecode_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using twoClkDecode_hdl_sv_wrapper_dut_t = VtwoClkDecode_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using twoClkDecode_hdl_sv_wrapper_dut_t = twoClkDecode_hdl_sv_wrapper;
#else
using twoClkDecode_hdl_sv_wrapper_dut_t = twoClkDecode_hdl_sv_wrapper;
#endif
struct _twoClkDecode_vl_registrar {
    _twoClkDecode_vl_registrar() {
        instanceFactory::registerBlock(
            "twoClkDecode_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<twoClkDecode_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "twoClk");
    }
};
static _twoClkDecode_vl_registrar _twoClkDecode_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
