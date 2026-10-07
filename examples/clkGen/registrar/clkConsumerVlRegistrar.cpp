//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=clkConsumer --parent=clkGen
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "clkConsumer_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VclkConsumer_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "clkConsumer_hdl_sv_wrapper.h"
#else
#include "clkConsumer_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using clkConsumer_hdl_sv_wrapper_dut_t = VclkConsumer_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using clkConsumer_hdl_sv_wrapper_dut_t = clkConsumer_hdl_sv_wrapper;
#else
using clkConsumer_hdl_sv_wrapper_dut_t = clkConsumer_hdl_sv_wrapper;
#endif
struct _clkConsumer_vl_registrar {
    _clkConsumer_vl_registrar() {
        instanceFactory::registerBlock(
            "clkConsumer_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<clkConsumer_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "clkGen");
    }
};
static _clkConsumer_vl_registrar _clkConsumer_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
