//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=mixed --parent=mixed_tb
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "mixed_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "Vmixed_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "mixed_hdl_sv_wrapper.h"
#else
#include "mixed_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using mixed_hdl_sv_wrapper_dut_t = Vmixed_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using mixed_hdl_sv_wrapper_dut_t = mixed_hdl_sv_wrapper;
#else
using mixed_hdl_sv_wrapper_dut_t = mixed_hdl_sv_wrapper;
#endif
struct _mixed_vl_registrar {
    _mixed_vl_registrar() {
        instanceFactory::registerBlock(
            "mixed_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<mixed_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "mixed");
        instanceFactory::registerBlock(
            "mixed_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<mixed_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "mixed");
    }
};
static _mixed_vl_registrar _mixed_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
