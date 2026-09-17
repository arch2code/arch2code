//

// GENERATED_CODE_PARAM --block=axi4sDemo --parent=axi4sDemo_tb
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "axi4sDemo_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "Vaxi4sDemo_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "axi4sDemo_hdl_sv_wrapper.h"
#else
#include "axi4sDemo_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using axi4sDemo_hdl_sv_wrapper_dut_t = Vaxi4sDemo_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using axi4sDemo_hdl_sv_wrapper_dut_t = axi4sDemo_hdl_sv_wrapper;
#else
using axi4sDemo_hdl_sv_wrapper_dut_t = axi4sDemo_hdl_sv_wrapper;
#endif
struct _axi4sDemo_vl_registrar {
    _axi4sDemo_vl_registrar() {
        instanceFactory::registerBlock(
            "axi4sDemo_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<axi4sDemo_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "axi4sDemo");
        instanceFactory::registerBlock(
            "axi4sDemo_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<axi4sDemo_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "axi4sDemo");
    }
};
static _axi4sDemo_vl_registrar _axi4sDemo_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
