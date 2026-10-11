//

// GENERATED_CODE_PARAM --block=vltSrc --parent=vltTop/../../yaml/vlt.yaml
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "vltSrc_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VvltSrc_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "vltSrc_hdl_sv_wrapper.h"
#else
#include "vltSrc_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using vltSrc_hdl_sv_wrapper_dut_t = VvltSrc_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using vltSrc_hdl_sv_wrapper_dut_t = vltSrc_hdl_sv_wrapper;
#else
using vltSrc_hdl_sv_wrapper_dut_t = vltSrc_hdl_sv_wrapper;
#endif
struct _vltSrc_vl_registrar {
    _vltSrc_vl_registrar() {
        instanceFactory::registerBlock(
            "vltSrc_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vltSrc_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "vlTiming");
    }
};
static _vltSrc_vl_registrar _vltSrc_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
