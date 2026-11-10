//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockD --parent=blockB/mixed.yaml
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "blockD_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VblockD_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "blockD_hdl_sv_wrapper.h"
#else
#include "blockD_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using blockD_hdl_sv_wrapper_dut_t = VblockD_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using blockD_hdl_sv_wrapper_dut_t = blockD_hdl_sv_wrapper;
#else
using blockD_hdl_sv_wrapper_dut_t = blockD_hdl_sv_wrapper;
#endif
struct _blockD_vl_registrar {
    _blockD_vl_registrar() {
        instanceFactory::registerBlock(
            "blockD_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockD_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "mixed");
    }
};
static _blockD_vl_registrar _blockD_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
