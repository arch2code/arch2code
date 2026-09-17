//

// GENERATED_CODE_PARAM --block=dut --parent=pySocket_tb
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "dut_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "Vdut_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "dut_hdl_sv_wrapper.h"
#else
#include "dut_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using dut_hdl_sv_wrapper_dut_t = Vdut_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using dut_hdl_sv_wrapper_dut_t = dut_hdl_sv_wrapper;
#else
using dut_hdl_sv_wrapper_dut_t = dut_hdl_sv_wrapper;
#endif
struct _dut_vl_registrar {
    _dut_vl_registrar() {
        instanceFactory::registerBlock(
            "dut_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<dut_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "pySocket");
        instanceFactory::registerBlock(
            "dut_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<dut_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "pySocket");
    }
};
static _dut_vl_registrar _dut_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
