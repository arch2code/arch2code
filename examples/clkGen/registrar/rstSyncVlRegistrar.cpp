//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=rstSync --parent=clkGen
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "rstSync_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VrstSync_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "rstSync_hdl_sv_wrapper.h"
#else
#include "rstSync_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using rstSync_hdl_sv_wrapper_dut_t = VrstSync_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using rstSync_hdl_sv_wrapper_dut_t = rstSync_hdl_sv_wrapper;
#else
using rstSync_hdl_sv_wrapper_dut_t = rstSync_hdl_sv_wrapper;
#endif
struct _rstSync_vl_registrar {
    _rstSync_vl_registrar() {
        instanceFactory::registerBlock(
            "rstSync_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<rstSync_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "clkGen");
    }
};
static _rstSync_vl_registrar _rstSync_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
