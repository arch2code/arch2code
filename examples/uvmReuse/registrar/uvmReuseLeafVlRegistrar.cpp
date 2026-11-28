//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseLeaf --parent=uvmReuseChain/../../yaml/uvmReuse.yaml
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT) || defined(QUESTA_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "uvmReuseLeaf_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "Vp13_uvmReuseChain_c12_uvmReuseLeaf_v8_hdl_sv_wrapper.h"
#include "VuvmReuseLeaf_w8_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "p13_uvmReuseChain_c12_uvmReuseLeaf_v8_hdl_sv_wrapper.h"
#include "uvmReuseLeaf_w8_hdl_sv_wrapper.h"
#elif defined(QUESTA_DUT)
#include "p13_uvmReuseChain_c12_uvmReuseLeaf_v8_hdl_sv_wrapper_questa.h"
#include "uvmReuseLeaf_w8_hdl_sv_wrapper_questa.h"
#else
#include "p13_uvmReuseChain_c12_uvmReuseLeaf_v8_hdl_sv_wrapper_xcelium.h"
#include "uvmReuseLeaf_w8_hdl_sv_wrapper_xcelium.h"
#endif
import uvmReuse.uvmReuseChain.config;
import uvmReuse.uvmReuseLeaf.config;
import uvmReuseLeaf.config;

namespace {
#if defined(VERILATOR)
using p13_uvmReuseChain_c12_uvmReuseLeaf_v8_hdl_sv_wrapper_dut_t = Vp13_uvmReuseChain_c12_uvmReuseLeaf_v8_hdl_sv_wrapper;
using uvmReuseLeaf_w8_hdl_sv_wrapper_dut_t = VuvmReuseLeaf_w8_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using p13_uvmReuseChain_c12_uvmReuseLeaf_v8_hdl_sv_wrapper_dut_t = p13_uvmReuseChain_c12_uvmReuseLeaf_v8_hdl_sv_wrapper;
using uvmReuseLeaf_w8_hdl_sv_wrapper_dut_t = uvmReuseLeaf_w8_hdl_sv_wrapper;
#elif defined(QUESTA_DUT)
using p13_uvmReuseChain_c12_uvmReuseLeaf_v8_hdl_sv_wrapper_dut_t = p13_uvmReuseChain_c12_uvmReuseLeaf_v8_hdl_sv_wrapper;
using uvmReuseLeaf_w8_hdl_sv_wrapper_dut_t = uvmReuseLeaf_w8_hdl_sv_wrapper;
#else
using p13_uvmReuseChain_c12_uvmReuseLeaf_v8_hdl_sv_wrapper_dut_t = p13_uvmReuseChain_c12_uvmReuseLeaf_v8_hdl_sv_wrapper;
using uvmReuseLeaf_w8_hdl_sv_wrapper_dut_t = uvmReuseLeaf_w8_hdl_sv_wrapper;
#endif
struct _uvmReuseLeaf_vl_registrar {
    _uvmReuseLeaf_vl_registrar() {
        instanceFactory::registerBlock(
            "uvmReuseLeaf_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseLeaf_hdl_sc_wrapper<p13_uvmReuseChain_c12_uvmReuseLeaf_v8_hdl_sv_wrapper_dut_t, uvmReuse_uvmReuseLeafFromChainConfig<uvmReuse_uvmReuseChainV8Config>>>(blockName, variant, bbMode));
            },
            "v8", "uvmReuse.uvmReuse_uvmReuseChain.uvmReuseLeaf");
        instanceFactory::registerBlock(
            "uvmReuseLeaf_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseLeaf_hdl_sc_wrapper<uvmReuseLeaf_w8_hdl_sv_wrapper_dut_t, uvmReuseLeafW8Config>>(blockName, variant, bbMode));
            },
            "w8", "uvmReuse.uvmReuse_uvmReuseChain.uvmReuseLeaf");
        instanceFactory::registerBlock(
            "uvmReuseLeaf_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseLeaf_hdl_sc_wrapper<uvmReuseLeaf_w8_hdl_sv_wrapper_dut_t, uvmReuseLeafW8Config>>(blockName, variant, bbMode));
            },
            "w8", "uvmReuseLeaf");
    }
};
static _uvmReuseLeaf_vl_registrar _uvmReuseLeaf_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT || QUESTA_DUT
// GENERATED_CODE_END
