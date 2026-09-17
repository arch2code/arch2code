//

// GENERATED_CODE_PARAM --block=hierVlDemo --parent=hierVlDemo_tb
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "hierVlDemo_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VhierVlDemo_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "hierVlDemo_hdl_sv_wrapper.h"
#else
#include "hierVlDemo_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using hierVlDemo_hdl_sv_wrapper_dut_t = VhierVlDemo_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using hierVlDemo_hdl_sv_wrapper_dut_t = hierVlDemo_hdl_sv_wrapper;
#else
using hierVlDemo_hdl_sv_wrapper_dut_t = hierVlDemo_hdl_sv_wrapper;
#endif
struct _hierVlDemo_vl_registrar {
    _hierVlDemo_vl_registrar() {
        instanceFactory::registerBlock(
            "hierVlDemo_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<hierVlDemo_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "hierVlDemo");
        instanceFactory::registerBlock(
            "hierVlDemo_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<hierVlDemo_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "hierVlDemo");
    }
};
static _hierVlDemo_vl_registrar _hierVlDemo_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
