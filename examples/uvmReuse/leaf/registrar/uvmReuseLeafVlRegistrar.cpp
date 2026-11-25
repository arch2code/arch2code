//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseLeaf --parent=uvmReuseLeaf_tb/../../yaml/uvmReuseLeaf_tb.yaml
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT) || defined(QUESTA_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "uvmReuseLeaf_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VuvmReuseLeaf_w4_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "uvmReuseLeaf_w4_hdl_sv_wrapper.h"
#elif defined(QUESTA_DUT)
#include "uvmReuseLeaf_w4_hdl_sv_wrapper_questa.h"
#else
#include "uvmReuseLeaf_w4_hdl_sv_wrapper_xcelium.h"
#endif
import uvmReuseLeaf.config;

namespace {
#if defined(VERILATOR)
using uvmReuseLeaf_w4_hdl_sv_wrapper_dut_t = VuvmReuseLeaf_w4_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using uvmReuseLeaf_w4_hdl_sv_wrapper_dut_t = uvmReuseLeaf_w4_hdl_sv_wrapper;
#elif defined(QUESTA_DUT)
using uvmReuseLeaf_w4_hdl_sv_wrapper_dut_t = uvmReuseLeaf_w4_hdl_sv_wrapper;
#else
using uvmReuseLeaf_w4_hdl_sv_wrapper_dut_t = uvmReuseLeaf_w4_hdl_sv_wrapper;
#endif
struct _uvmReuseLeaf_vl_registrar {
    _uvmReuseLeaf_vl_registrar() {
        instanceFactory::registerBlock(
            "uvmReuseLeaf_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseLeaf_hdl_sc_wrapper<uvmReuseLeaf_w4_hdl_sv_wrapper_dut_t, uvmReuseLeafW4Config>>(blockName, variant, bbMode));
            },
            "w4", "uvmReuseLeaf");
        instanceFactory::registerBlock(
            "uvmReuseLeaf_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseLeaf_hdl_sc_wrapper<uvmReuseLeaf_w4_hdl_sv_wrapper_dut_t, uvmReuseLeafW4Config>>(blockName, variant, bbMode));
            },
            "w4", "uvmReuseLeaf.uvmReuseLeaf_tb.uvmReuseLeaf");
    }
};
static _uvmReuseLeaf_vl_registrar _uvmReuseLeaf_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT || QUESTA_DUT
// GENERATED_CODE_END
