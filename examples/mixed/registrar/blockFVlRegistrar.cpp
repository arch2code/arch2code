//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockF --parent=blockB
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "blockF_hdl_sc_wrapper.h"
#include "VblockF_variant0_hdl_sv_wrapper.h"
#include "VblockF_variant1_hdl_sv_wrapper.h"
#include "mixedVariantConfig.h"

namespace {
struct _blockF_vl_registrar {
    _blockF_vl_registrar() {
        instanceFactory::registerBlock(
            "blockF_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockF_hdl_sc_wrapper<VblockF_variant0_hdl_sv_wrapper, blockFVariant0Config>>(blockName, variant, bbMode));
            },
            "variant0", "mixed");
        instanceFactory::registerBlock(
            "blockF_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockF_hdl_sc_wrapper<VblockF_variant0_hdl_sv_wrapper, blockFVariant0Config>>(blockName, variant, bbMode));
            },
            "variant0", "mixed.mixed_blockB.mixed_blockF");
        instanceFactory::registerBlock(
            "blockF_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockF_hdl_sc_wrapper<VblockF_variant1_hdl_sv_wrapper, blockFVariant1Config>>(blockName, variant, bbMode));
            },
            "variant1", "mixed");
        instanceFactory::registerBlock(
            "blockF_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockF_hdl_sc_wrapper<VblockF_variant1_hdl_sv_wrapper, blockFVariant1Config>>(blockName, variant, bbMode));
            },
            "variant1", "mixed.mixed_blockB.mixed_blockF");
    }
};
static _blockF_vl_registrar _blockF_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
