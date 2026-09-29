//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtPrimeDecode --parent=xpRtInhTop/../../yaml/xpRtInh.yaml
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "xpRtPrimeDecode_hdl_sc_wrapper.h"
#include "VxpRtPrimeDecode_hdl_sv_wrapper.h"

namespace {
struct _xpRtPrimeDecode_vl_registrar {
    _xpRtPrimeDecode_vl_registrar() {
        instanceFactory::registerBlock(
            "xpRtPrimeDecode_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpRtPrimeDecode_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "xpRtInh");
        instanceFactory::registerBlock(
            "xpRtPrimeDecode_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpRtPrimeDecode_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "xpRtInh");
    }
};
static _xpRtPrimeDecode_vl_registrar _xpRtPrimeDecode_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
