//

// GENERATED_CODE_PARAM --block=vliLeaf --parent=vliWrap/../../yaml/vliCont.yaml
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "vliLeaf_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "Vp13_vlInh_vliCont_c13_vlInh_vliLeaf_alt_hdl_sv_wrapper.h"
#include "Vp13_vlInh_vliCont_c13_vlInh_vliLeaf_default_hdl_sv_wrapper.h"
#include "VvliLeaf_solo_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "p13_vlInh_vliCont_c13_vlInh_vliLeaf_alt_hdl_sv_wrapper.h"
#include "p13_vlInh_vliCont_c13_vlInh_vliLeaf_default_hdl_sv_wrapper.h"
#include "vliLeaf_solo_hdl_sv_wrapper.h"
#else
#include "p13_vlInh_vliCont_c13_vlInh_vliLeaf_alt_hdl_sv_wrapper_xcelium.h"
#include "p13_vlInh_vliCont_c13_vlInh_vliLeaf_default_hdl_sv_wrapper_xcelium.h"
#include "vliLeaf_solo_hdl_sv_wrapper_xcelium.h"
#endif
import vlInh.vliCont.config;
import vlInh.vliLeaf.config;

namespace {
#if defined(VERILATOR)
using p13_vlInh_vliCont_c13_vlInh_vliLeaf_alt_hdl_sv_wrapper_dut_t = Vp13_vlInh_vliCont_c13_vlInh_vliLeaf_alt_hdl_sv_wrapper;
using p13_vlInh_vliCont_c13_vlInh_vliLeaf_default_hdl_sv_wrapper_dut_t = Vp13_vlInh_vliCont_c13_vlInh_vliLeaf_default_hdl_sv_wrapper;
using vliLeaf_solo_hdl_sv_wrapper_dut_t = VvliLeaf_solo_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using p13_vlInh_vliCont_c13_vlInh_vliLeaf_alt_hdl_sv_wrapper_dut_t = p13_vlInh_vliCont_c13_vlInh_vliLeaf_alt_hdl_sv_wrapper;
using p13_vlInh_vliCont_c13_vlInh_vliLeaf_default_hdl_sv_wrapper_dut_t = p13_vlInh_vliCont_c13_vlInh_vliLeaf_default_hdl_sv_wrapper;
using vliLeaf_solo_hdl_sv_wrapper_dut_t = vliLeaf_solo_hdl_sv_wrapper;
#else
using p13_vlInh_vliCont_c13_vlInh_vliLeaf_alt_hdl_sv_wrapper_dut_t = p13_vlInh_vliCont_c13_vlInh_vliLeaf_alt_hdl_sv_wrapper;
using p13_vlInh_vliCont_c13_vlInh_vliLeaf_default_hdl_sv_wrapper_dut_t = p13_vlInh_vliCont_c13_vlInh_vliLeaf_default_hdl_sv_wrapper;
using vliLeaf_solo_hdl_sv_wrapper_dut_t = vliLeaf_solo_hdl_sv_wrapper;
#endif
static_assert(vliSt<vlInh_vliLeafSourcedConfig<vlInh_vliContAltConfig>>::_bitWidth == 42, "p13_vlInh_vliCont_c13_vlInh_vliLeaf_alt_hdl_sv_wrapper: out_data width differs from the generated boundary");
static_assert(vliSt<vlInh_vliLeafSourcedConfig<vlInh_vliContAltConfig>>::_bitWidth == 42, "p13_vlInh_vliCont_c13_vlInh_vliLeaf_alt_hdl_sv_wrapper: in_data width differs from the generated boundary");
static_assert(vliSt<vlInh_vliLeafSourcedConfig<vlInh_vliContDefaultConfig>>::_bitWidth == 40, "p13_vlInh_vliCont_c13_vlInh_vliLeaf_default_hdl_sv_wrapper: out_data width differs from the generated boundary");
static_assert(vliSt<vlInh_vliLeafSourcedConfig<vlInh_vliContDefaultConfig>>::_bitWidth == 40, "p13_vlInh_vliCont_c13_vlInh_vliLeaf_default_hdl_sv_wrapper: in_data width differs from the generated boundary");
static_assert(vliSt<vlInh_vliLeafSoloConfig>::_bitWidth == 40, "vliLeaf_solo_hdl_sv_wrapper: out_data width differs from the generated boundary");
static_assert(vliSt<vlInh_vliLeafSoloConfig>::_bitWidth == 40, "vliLeaf_solo_hdl_sv_wrapper: in_data width differs from the generated boundary");
struct _vliLeaf_vl_registrar {
    _vliLeaf_vl_registrar() {
        instanceFactory::registerBlock(
            "vliLeaf_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliLeaf_hdl_sc_wrapper<p13_vlInh_vliCont_c13_vlInh_vliLeaf_alt_hdl_sv_wrapper_dut_t, vlInh_vliLeafSourcedConfig<vlInh_vliContAltConfig>>>(blockName, variant, bbMode));
            },
            "alt", "vlInh.vlInh_vliCont.vlInh_vliLeaf");
        instanceFactory::registerBlock(
            "vliLeaf_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliLeaf_hdl_sc_wrapper<p13_vlInh_vliCont_c13_vlInh_vliLeaf_default_hdl_sv_wrapper_dut_t, vlInh_vliLeafSourcedConfig<vlInh_vliContDefaultConfig>>>(blockName, variant, bbMode));
            },
            "default", "vlInh.vlInh_vliCont.vlInh_vliLeaf");
        instanceFactory::registerBlock(
            "vliLeaf_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliLeaf_hdl_sc_wrapper<vliLeaf_solo_hdl_sv_wrapper_dut_t, vlInh_vliLeafSoloConfig>>(blockName, variant, bbMode));
            },
            "solo", "vlInh");
        instanceFactory::registerBlock(
            "vliLeaf_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliLeaf_hdl_sc_wrapper<vliLeaf_solo_hdl_sv_wrapper_dut_t, vlInh_vliLeafSoloConfig>>(blockName, variant, bbMode));
            },
            "solo", "vlInh.vlInh_vliCont.vlInh_vliLeaf");
        instanceFactory::registerBlock(
            "vliLeaf_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliLeaf_hdl_sc_wrapper<vliLeaf_solo_hdl_sv_wrapper_dut_t, vlInh_vliLeafSoloConfig>>(blockName, variant, bbMode));
            },
            "solo", "vlInh.vlInh_vliWrap.vlInh_vliLeaf");
    }
};
static _vliLeaf_vl_registrar _vliLeaf_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
