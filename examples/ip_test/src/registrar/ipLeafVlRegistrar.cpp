//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipLeaf --parent=src
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "ipLeaf_hdl_sc_wrapper.h"
#include "VipLeaf_variantLeaf0_hdl_sv_wrapper.h"
#include "ipLeafVariantConfig.h"

namespace {
struct _ipLeaf_vl_registrar {
    _ipLeaf_vl_registrar() {
        instanceFactory::registerBlock(
            "ipLeaf_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ipLeaf_hdl_sc_wrapper<VipLeaf_variantLeaf0_hdl_sv_wrapper, ipLeafVariantLeaf0Config>>(blockName, variant, bbMode));
            },
            "variantLeaf0", "ip_test");
        instanceFactory::registerBlock(
            "ipLeaf_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ipLeaf_hdl_sc_wrapper<VipLeaf_variantLeaf0_hdl_sv_wrapper, ipLeafVariantLeaf0Config>>(blockName, variant, bbMode));
            },
            "variantLeaf0", "ip_test.ip_test_src.ip_test_ipLeaf");
    }
};
static _ipLeaf_vl_registrar _ipLeaf_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
