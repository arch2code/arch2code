//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=producer --parent=simple
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "producer_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "Vproducer_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "producer_hdl_sv_wrapper.h"
#else
#include "producer_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using producer_hdl_sv_wrapper_dut_t = Vproducer_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using producer_hdl_sv_wrapper_dut_t = producer_hdl_sv_wrapper;
#else
using producer_hdl_sv_wrapper_dut_t = producer_hdl_sv_wrapper;
#endif
struct _producer_vl_registrar {
    _producer_vl_registrar() {
        instanceFactory::registerBlock(
            "producer_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<producer_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "simple");
    }
};
static _producer_vl_registrar _producer_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
