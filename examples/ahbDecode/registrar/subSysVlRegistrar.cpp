//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=subSys --parent=ahbSoc/ahbDecode.yaml
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "subSys_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VsubSys_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "subSys_hdl_sv_wrapper.h"
#else
#include "subSys_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using subSys_hdl_sv_wrapper_dut_t = VsubSys_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using subSys_hdl_sv_wrapper_dut_t = subSys_hdl_sv_wrapper;
#else
using subSys_hdl_sv_wrapper_dut_t = subSys_hdl_sv_wrapper;
#endif
struct _subSys_vl_registrar {
    _subSys_vl_registrar() {
        instanceFactory::registerBlock(
            "subSys_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<subSys_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "ahbDecode");
    }
};
static _subSys_vl_registrar _subSys_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
