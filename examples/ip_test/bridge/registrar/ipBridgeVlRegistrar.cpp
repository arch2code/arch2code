//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipBridge --parent=bridgeStdTop
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "ipBridge_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VipBridge_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "ipBridge_hdl_sv_wrapper.h"
#else
#include "ipBridge_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using ipBridge_hdl_sv_wrapper_dut_t = VipBridge_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using ipBridge_hdl_sv_wrapper_dut_t = ipBridge_hdl_sv_wrapper;
#else
using ipBridge_hdl_sv_wrapper_dut_t = ipBridge_hdl_sv_wrapper;
#endif
struct _ipBridge_vl_registrar {
    _ipBridge_vl_registrar() {
        instanceFactory::registerBlock(
            "ipBridge_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ipBridge_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "ipBridge");
        instanceFactory::registerBlock(
            "ipBridge_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ipBridge_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "ipBridge");
    }
};
static _ipBridge_vl_registrar _ipBridge_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
