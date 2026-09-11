//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtNestDecode --parent=xpRtWrap/../../yaml/xpRtInh.yaml
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpRtNestDecode_hdl_sc_wrapper.h"
#include "Vp16_xpRtInh_xpRtWrap_c22_xpRtInh_xpRtNestDecode_use_hdl_sv_wrapper.h"
import xpRtInh.xpRtWrap.config;

namespace {
struct _xpRtNestDecode_vl_registrar {
    _xpRtNestDecode_vl_registrar() {
        instanceFactory::registerBlock(
            "xpRtNestDecode_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpRtNestDecode_hdl_sc_wrapper<Vp16_xpRtInh_xpRtWrap_c22_xpRtInh_xpRtNestDecode_use_hdl_sv_wrapper, xpRtInh_xpRtWrapUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpRtInh.xpRtInh_xpRtWrap.xpRtInh_xpRtNestDecode");
    }
};
static _xpRtNestDecode_vl_registrar _xpRtNestDecode_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
