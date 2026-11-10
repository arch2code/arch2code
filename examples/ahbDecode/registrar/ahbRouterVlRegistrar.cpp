//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ahbRouter --parent=ahbSoc/ahbDecode.yaml
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "ahbRouter_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VahbRouter_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "ahbRouter_hdl_sv_wrapper.h"
#else
#include "ahbRouter_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using ahbRouter_hdl_sv_wrapper_dut_t = VahbRouter_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using ahbRouter_hdl_sv_wrapper_dut_t = ahbRouter_hdl_sv_wrapper;
#else
using ahbRouter_hdl_sv_wrapper_dut_t = ahbRouter_hdl_sv_wrapper;
#endif
struct _ahbRouter_vl_registrar {
    _ahbRouter_vl_registrar() {
        instanceFactory::registerBlock(
            "ahbRouter_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ahbRouter_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "ahbDecode");
    }
};
static _ahbRouter_vl_registrar _ahbRouter_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
