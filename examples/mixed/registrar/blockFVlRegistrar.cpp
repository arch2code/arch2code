//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockF --parent=blockB
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "blockF_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VblockF_variant0_hdl_sv_wrapper.h"
#include "VblockF_variant1_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "blockF_variant0_hdl_sv_wrapper.h"
#include "blockF_variant1_hdl_sv_wrapper.h"
#else
#include "blockF_variant0_hdl_sv_wrapper_xcelium.h"
#include "blockF_variant1_hdl_sv_wrapper_xcelium.h"
#endif
import mixed.blockF.config;

namespace {
#if defined(VERILATOR)
using blockF_variant0_hdl_sv_wrapper_dut_t = VblockF_variant0_hdl_sv_wrapper;
using blockF_variant1_hdl_sv_wrapper_dut_t = VblockF_variant1_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using blockF_variant0_hdl_sv_wrapper_dut_t = blockF_variant0_hdl_sv_wrapper;
using blockF_variant1_hdl_sv_wrapper_dut_t = blockF_variant1_hdl_sv_wrapper;
#else
using blockF_variant0_hdl_sv_wrapper_dut_t = blockF_variant0_hdl_sv_wrapper;
using blockF_variant1_hdl_sv_wrapper_dut_t = blockF_variant1_hdl_sv_wrapper;
#endif
struct _blockF_vl_registrar {
    _blockF_vl_registrar() {
        instanceFactory::registerBlock(
            "blockF_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockF_hdl_sc_wrapper<blockF_variant0_hdl_sv_wrapper_dut_t, mixed_blockFVariant0Config>>(blockName, variant, bbMode));
            },
            "variant0", "mixed");
        instanceFactory::registerBlock(
            "blockF_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockF_hdl_sc_wrapper<blockF_variant0_hdl_sv_wrapper_dut_t, mixed_blockFVariant0Config>>(blockName, variant, bbMode));
            },
            "variant0", "mixed.mixed_blockB.mixed_blockF");
        instanceFactory::registerBlock(
            "blockF_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockF_hdl_sc_wrapper<blockF_variant1_hdl_sv_wrapper_dut_t, mixed_blockFVariant1Config>>(blockName, variant, bbMode));
            },
            "variant1", "mixed");
        instanceFactory::registerBlock(
            "blockF_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockF_hdl_sc_wrapper<blockF_variant1_hdl_sv_wrapper_dut_t, mixed_blockFVariant1Config>>(blockName, variant, bbMode));
            },
            "variant1", "mixed.mixed_blockB.mixed_blockF");
    }
};
static _blockF_vl_registrar _blockF_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
