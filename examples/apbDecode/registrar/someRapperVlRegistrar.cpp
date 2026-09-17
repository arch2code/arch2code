//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=someRapper --parent=top
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "someRapper_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VsomeRapper_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "someRapper_hdl_sv_wrapper.h"
#else
#include "someRapper_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using someRapper_hdl_sv_wrapper_dut_t = VsomeRapper_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using someRapper_hdl_sv_wrapper_dut_t = someRapper_hdl_sv_wrapper;
#else
using someRapper_hdl_sv_wrapper_dut_t = someRapper_hdl_sv_wrapper;
#endif
struct _someRapper_vl_registrar {
    _someRapper_vl_registrar() {
        instanceFactory::registerBlock(
            "someRapper_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<someRapper_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "apbDecode");
        instanceFactory::registerBlock(
            "someRapper_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<someRapper_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "apbDecode");
    }
};
static _someRapper_vl_registrar _someRapper_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
