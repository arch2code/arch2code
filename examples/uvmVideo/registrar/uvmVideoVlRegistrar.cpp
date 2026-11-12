//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmVideo --parent=uvmVideo_tb/../../yaml/uvmVideo.yaml
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "uvmVideo_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VuvmVideo_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "uvmVideo_hdl_sv_wrapper.h"
#else
#include "uvmVideo_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using uvmVideo_hdl_sv_wrapper_dut_t = VuvmVideo_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using uvmVideo_hdl_sv_wrapper_dut_t = uvmVideo_hdl_sv_wrapper;
#else
using uvmVideo_hdl_sv_wrapper_dut_t = uvmVideo_hdl_sv_wrapper;
#endif
struct _uvmVideo_vl_registrar {
    _uvmVideo_vl_registrar() {
        instanceFactory::registerBlock(
            "uvmVideo_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmVideo_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "uvmVideo");
    }
};
static _uvmVideo_vl_registrar _uvmVideo_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
