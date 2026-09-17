//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=axiDemo --parent=axiDemo_tb
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "axiDemo_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VaxiDemo_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "axiDemo_hdl_sv_wrapper.h"
#else
#include "axiDemo_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using axiDemo_hdl_sv_wrapper_dut_t = VaxiDemo_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using axiDemo_hdl_sv_wrapper_dut_t = axiDemo_hdl_sv_wrapper;
#else
using axiDemo_hdl_sv_wrapper_dut_t = axiDemo_hdl_sv_wrapper;
#endif
struct _axiDemo_vl_registrar {
    _axiDemo_vl_registrar() {
        instanceFactory::registerBlock(
            "axiDemo_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<axiDemo_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "axiDemo");
        instanceFactory::registerBlock(
            "axiDemo_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<axiDemo_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "axiDemo");
    }
};
static _axiDemo_vl_registrar _axiDemo_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
