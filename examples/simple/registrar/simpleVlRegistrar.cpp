//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=simple --parent=simple_tb
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "simple_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "Vsimple_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "simple_hdl_sv_wrapper.h"
#else
#include "simple_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using simple_hdl_sv_wrapper_dut_t = Vsimple_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using simple_hdl_sv_wrapper_dut_t = simple_hdl_sv_wrapper;
#else
using simple_hdl_sv_wrapper_dut_t = simple_hdl_sv_wrapper;
#endif
struct _simple_vl_registrar {
    _simple_vl_registrar() {
        instanceFactory::registerBlock(
            "simple_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<simple_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "simple");
        instanceFactory::registerBlock(
            "simple_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<simple_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "simple");
    }
};
static _simple_vl_registrar _simple_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
