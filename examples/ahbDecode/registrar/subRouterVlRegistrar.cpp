//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=subRouter --parent=subSys/ahbDecode.yaml
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "subRouter_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VsubRouter_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "subRouter_hdl_sv_wrapper.h"
#else
#include "subRouter_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using subRouter_hdl_sv_wrapper_dut_t = VsubRouter_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using subRouter_hdl_sv_wrapper_dut_t = subRouter_hdl_sv_wrapper;
#else
using subRouter_hdl_sv_wrapper_dut_t = subRouter_hdl_sv_wrapper;
#endif
struct _subRouter_vl_registrar {
    _subRouter_vl_registrar() {
        instanceFactory::registerBlock(
            "subRouter_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<subRouter_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "ahbDecode");
    }
};
static _subRouter_vl_registrar _subRouter_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
