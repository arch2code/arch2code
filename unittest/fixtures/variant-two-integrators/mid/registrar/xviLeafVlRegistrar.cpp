//

// GENERATED_CODE_PARAM --block=xviLeaf --parent=xviMid/../../yaml/xviMid.yaml
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "xviLeaf_hdl_sc_wrapper.h"
#include "VxviMid_xviLeaf_v0_hdl_sv_wrapper.h"
#include "VxviMid_xviLeaf_vMid_hdl_sv_wrapper.h"
#include "xviLeafVariantConfig.h"
import xviMid.xviLeaf.config;

namespace {
struct _xviLeaf_vl_registrar {
    _xviLeaf_vl_registrar() {
        instanceFactory::registerBlock(
            "xviLeaf_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviLeaf_hdl_sc_wrapper<VxviMid_xviLeaf_v0_hdl_sv_wrapper, xviMid_xviLeafV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xviLeaf");
        instanceFactory::registerBlock(
            "xviLeaf_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviLeaf_hdl_sc_wrapper<VxviMid_xviLeaf_v0_hdl_sv_wrapper, xviMid_xviLeafV0Config>>(blockName, variant, bbMode));
            },
            "v0", "xviMid.xviMid.xviLeaf");
        instanceFactory::registerBlock(
            "xviLeaf_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviLeaf_hdl_sc_wrapper<VxviMid_xviLeaf_vMid_hdl_sv_wrapper, xviMid_xviLeafVMidConfig>>(blockName, variant, bbMode));
            },
            "vMid", "xviLeaf");
        instanceFactory::registerBlock(
            "xviLeaf_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xviLeaf_hdl_sc_wrapper<VxviMid_xviLeaf_vMid_hdl_sv_wrapper, xviMid_xviLeafVMidConfig>>(blockName, variant, bbMode));
            },
            "vMid", "xviMid.xviMid.xviLeaf");
    }
};
static _xviLeaf_vl_registrar _xviLeaf_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
