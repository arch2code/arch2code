//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtInhTop --parent=xpRtInhTop_tb/../../yaml/xpRtInh.yaml
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpRtInhTop_hdl_sc_wrapper.h"
#include "VxpRtInhTop_hdl_sv_wrapper.h"

namespace {
struct _xpRtInhTop_vl_registrar {
    _xpRtInhTop_vl_registrar() {
        instanceFactory::registerBlock(
            "xpRtInhTop_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpRtInhTop_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "xpRtInh");
        instanceFactory::registerBlock(
            "xpRtInhTop_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpRtInhTop_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "xpRtInh");
    }
};
static _xpRtInhTop_vl_registrar _xpRtInhTop_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
