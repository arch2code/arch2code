//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtWrap --parent=xpRtInhTop/../../yaml/xpRtInh.yaml
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpRtWrap_hdl_sc_wrapper.h"
#include "VxpRtWrap_use_hdl_sv_wrapper.h"
import xpRtInh.xpRtWrap.config;

namespace {
struct _xpRtWrap_vl_registrar {
    _xpRtWrap_vl_registrar() {
        instanceFactory::registerBlock(
            "xpRtWrap_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpRtWrap_hdl_sc_wrapper<VxpRtWrap_use_hdl_sv_wrapper, xpRtInh_xpRtWrapUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpRtInh");
        instanceFactory::registerBlock(
            "xpRtWrap_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpRtWrap_hdl_sc_wrapper<VxpRtWrap_use_hdl_sv_wrapper, xpRtInh_xpRtWrapUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpRtInh.xpRtInh_xpRtInhTop.xpRtInh_xpRtWrap");
    }
};
static _xpRtWrap_vl_registrar _xpRtWrap_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
