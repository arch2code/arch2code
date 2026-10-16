//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkIpSrc --parent=twoClk
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "twoClkIpSrc_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VtwoClkIpSrc_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "twoClkIpSrc_hdl_sv_wrapper.h"
#else
#include "twoClkIpSrc_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using twoClkIpSrc_hdl_sv_wrapper_dut_t = VtwoClkIpSrc_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using twoClkIpSrc_hdl_sv_wrapper_dut_t = twoClkIpSrc_hdl_sv_wrapper;
#else
using twoClkIpSrc_hdl_sv_wrapper_dut_t = twoClkIpSrc_hdl_sv_wrapper;
#endif
struct _twoClkIpSrc_vl_registrar {
    _twoClkIpSrc_vl_registrar() {
        instanceFactory::registerBlock(
            "twoClkIpSrc_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<twoClkIpSrc_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "twoClkIp");
    }
};
static _twoClkIpSrc_vl_registrar _twoClkIpSrc_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
