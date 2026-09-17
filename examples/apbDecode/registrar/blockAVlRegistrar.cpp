//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockA --parent=someRapper
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "blockA_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VblockA_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "blockA_hdl_sv_wrapper.h"
#else
#include "blockA_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using blockA_hdl_sv_wrapper_dut_t = VblockA_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using blockA_hdl_sv_wrapper_dut_t = blockA_hdl_sv_wrapper;
#else
using blockA_hdl_sv_wrapper_dut_t = blockA_hdl_sv_wrapper;
#endif
struct _blockA_vl_registrar {
    _blockA_vl_registrar() {
        instanceFactory::registerBlock(
            "blockA_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockA_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "apbDecode");
        instanceFactory::registerBlock(
            "blockA_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockA_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "apbDecode");
    }
};
static _blockA_vl_registrar _blockA_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
