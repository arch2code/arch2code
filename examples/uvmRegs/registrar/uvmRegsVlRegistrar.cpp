//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegs --parent=uvmRegs_tb/../../yaml/uvmRegs.yaml
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "uvmRegs_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VuvmRegs_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "uvmRegs_hdl_sv_wrapper.h"
#else
#include "uvmRegs_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using uvmRegs_hdl_sv_wrapper_dut_t = VuvmRegs_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using uvmRegs_hdl_sv_wrapper_dut_t = uvmRegs_hdl_sv_wrapper;
#else
using uvmRegs_hdl_sv_wrapper_dut_t = uvmRegs_hdl_sv_wrapper;
#endif
struct _uvmRegs_vl_registrar {
    _uvmRegs_vl_registrar() {
        instanceFactory::registerBlock(
            "uvmRegs_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmRegs_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "uvmRegs");
    }
};
static _uvmRegs_vl_registrar _uvmRegs_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
