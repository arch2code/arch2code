//

// GENERATED_CODE_PARAM --block=pySocket --parent=pySocket_tb
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "pySocket_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VpySocket_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "pySocket_hdl_sv_wrapper.h"
#else
#include "pySocket_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using pySocket_hdl_sv_wrapper_dut_t = VpySocket_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using pySocket_hdl_sv_wrapper_dut_t = pySocket_hdl_sv_wrapper;
#else
using pySocket_hdl_sv_wrapper_dut_t = pySocket_hdl_sv_wrapper;
#endif
struct _pySocket_vl_registrar {
    _pySocket_vl_registrar() {
        instanceFactory::registerBlock(
            "pySocket_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<pySocket_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "pySocket");
        instanceFactory::registerBlock(
            "pySocket_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<pySocket_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "pySocket");
    }
};
static _pySocket_vl_registrar _pySocket_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
