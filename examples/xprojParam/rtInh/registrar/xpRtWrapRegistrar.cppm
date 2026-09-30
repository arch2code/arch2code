//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtWrap --parent=xpRtInhTop/../../yaml/xpRtInh.yaml
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module xpRtInh.xpRtInh_xpRtWrap.registrar;
import xpRtInh_xpRtWrap.block;
import xpRtInh.xpRtWrap.config;

namespace {
struct _xpRtWrap_registrar {
    _xpRtWrap_registrar() {
        instanceFactory::registerBlock(
            "xpRtWrap_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpRtWrap<xpRtInh_xpRtWrapUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpRtInh");
        instanceFactory::registerBlock(
            "xpRtWrap_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpRtWrap<xpRtInh_xpRtWrapUseConfig>>(blockName, variant, bbMode));
            },
            "use", "xpRtInh.xpRtInh_xpRtInhTop.xpRtInh_xpRtWrap");
    }
};
static _xpRtWrap_registrar _xpRtWrap_registrar_instance;
} // namespace
// GENERATED_CODE_END
