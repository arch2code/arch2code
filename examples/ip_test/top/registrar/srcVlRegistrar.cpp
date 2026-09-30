//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=src --parent=ip_top
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "src_hdl_sc_wrapper.h"
#include "Vsrc_variantSrc0_hdl_sv_wrapper.h"
import ip_test.src.config;

namespace {
struct _src_vl_registrar {
    _src_vl_registrar() {
        instanceFactory::registerBlock(
            "src_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<src_hdl_sc_wrapper<Vsrc_variantSrc0_hdl_sv_wrapper, ip_test_srcVariantSrc0Config>>(blockName, variant, bbMode));
            },
            "variantSrc0", "ip_test");
        instanceFactory::registerBlock(
            "src_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<src_hdl_sc_wrapper<Vsrc_variantSrc0_hdl_sv_wrapper, ip_test_srcVariantSrc0Config>>(blockName, variant, bbMode));
            },
            "variantSrc0", "ip_test.ip_test_ip_top.ip_test_src");
    }
};
static _src_vl_registrar _src_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
