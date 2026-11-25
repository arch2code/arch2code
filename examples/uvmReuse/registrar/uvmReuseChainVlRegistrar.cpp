//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseChain --parent=uvmReuse_tb/../../yaml/uvmReuse.yaml
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT) || defined(QUESTA_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "uvmReuseChain_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VuvmReuseChain_v8_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "uvmReuseChain_v8_hdl_sv_wrapper.h"
#elif defined(QUESTA_DUT)
#include "uvmReuseChain_v8_hdl_sv_wrapper_questa.h"
#else
#include "uvmReuseChain_v8_hdl_sv_wrapper_xcelium.h"
#endif
import uvmReuse.uvmReuseChain.config;

namespace {
#if defined(VERILATOR)
using uvmReuseChain_v8_hdl_sv_wrapper_dut_t = VuvmReuseChain_v8_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using uvmReuseChain_v8_hdl_sv_wrapper_dut_t = uvmReuseChain_v8_hdl_sv_wrapper;
#elif defined(QUESTA_DUT)
using uvmReuseChain_v8_hdl_sv_wrapper_dut_t = uvmReuseChain_v8_hdl_sv_wrapper;
#else
using uvmReuseChain_v8_hdl_sv_wrapper_dut_t = uvmReuseChain_v8_hdl_sv_wrapper;
#endif
struct _uvmReuseChain_vl_registrar {
    _uvmReuseChain_vl_registrar() {
        instanceFactory::registerBlock(
            "uvmReuseChain_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseChain_hdl_sc_wrapper<uvmReuseChain_v8_hdl_sv_wrapper_dut_t, uvmReuse_uvmReuseChainV8Config>>(blockName, variant, bbMode));
            },
            "v8", "uvmReuse");
        instanceFactory::registerBlock(
            "uvmReuseChain_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseChain_hdl_sc_wrapper<uvmReuseChain_v8_hdl_sv_wrapper_dut_t, uvmReuse_uvmReuseChainV8Config>>(blockName, variant, bbMode));
            },
            "v8", "uvmReuse.uvmReuse_tb.uvmReuse_uvmReuseChain");
    }
};
static _uvmReuseChain_vl_registrar _uvmReuseChain_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT || QUESTA_DUT
// GENERATED_CODE_END
