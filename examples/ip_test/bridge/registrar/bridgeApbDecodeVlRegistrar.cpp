//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=bridgeApbDecode --parent=ipBridge
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "bridgeApbDecode_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VbridgeApbDecode_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "bridgeApbDecode_hdl_sv_wrapper.h"
#else
#include "bridgeApbDecode_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using bridgeApbDecode_hdl_sv_wrapper_dut_t = VbridgeApbDecode_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using bridgeApbDecode_hdl_sv_wrapper_dut_t = bridgeApbDecode_hdl_sv_wrapper;
#else
using bridgeApbDecode_hdl_sv_wrapper_dut_t = bridgeApbDecode_hdl_sv_wrapper;
#endif
struct _bridgeApbDecode_vl_registrar {
    _bridgeApbDecode_vl_registrar() {
        instanceFactory::registerBlock(
            "bridgeApbDecode_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<bridgeApbDecode_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "ipBridge");
        instanceFactory::registerBlock(
            "bridgeApbDecode_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<bridgeApbDecode_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "ipBridge");
    }
};
static _bridgeApbDecode_vl_registrar _bridgeApbDecode_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
