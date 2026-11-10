//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=leafA --parent=ahbSoc/ahbDecode.yaml
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "leafA_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VleafA_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "leafA_hdl_sv_wrapper.h"
#else
#include "leafA_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using leafA_hdl_sv_wrapper_dut_t = VleafA_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using leafA_hdl_sv_wrapper_dut_t = leafA_hdl_sv_wrapper;
#else
using leafA_hdl_sv_wrapper_dut_t = leafA_hdl_sv_wrapper;
#endif
struct _leafA_vl_registrar {
    _leafA_vl_registrar() {
        instanceFactory::registerBlock(
            "leafA_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<leafA_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "ahbDecode");
    }
};
static _leafA_vl_registrar _leafA_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
