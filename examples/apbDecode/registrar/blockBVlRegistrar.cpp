//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockB --parent=someRapper
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "blockB_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VblockB_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "blockB_hdl_sv_wrapper.h"
#else
#include "blockB_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using blockB_hdl_sv_wrapper_dut_t = VblockB_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using blockB_hdl_sv_wrapper_dut_t = blockB_hdl_sv_wrapper;
#else
using blockB_hdl_sv_wrapper_dut_t = blockB_hdl_sv_wrapper;
#endif
struct _blockB_vl_registrar {
    _blockB_vl_registrar() {
        instanceFactory::registerBlock(
            "blockB_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockB_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "apbDecode");
        instanceFactory::registerBlock(
            "blockB_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockB_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "apbDecode");
    }
};
static _blockB_vl_registrar _blockB_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
