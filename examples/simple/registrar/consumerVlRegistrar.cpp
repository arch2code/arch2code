//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=consumer --parent=simple
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "consumer_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "Vconsumer_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "consumer_hdl_sv_wrapper.h"
#else
#include "consumer_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using consumer_hdl_sv_wrapper_dut_t = Vconsumer_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using consumer_hdl_sv_wrapper_dut_t = consumer_hdl_sv_wrapper;
#else
using consumer_hdl_sv_wrapper_dut_t = consumer_hdl_sv_wrapper;
#endif
struct _consumer_vl_registrar {
    _consumer_vl_registrar() {
        instanceFactory::registerBlock(
            "consumer_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<consumer_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "simple");
    }
};
static _consumer_vl_registrar _consumer_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
