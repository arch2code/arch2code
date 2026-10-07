//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkIpSrc --parent=twoClk
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "twoClkIpSrc_hdl_sc_wrapper.h"
#include "VtwoClkIpSrc_hdl_sv_wrapper.h"

namespace {
struct _twoClkIpSrc_vl_registrar {
    _twoClkIpSrc_vl_registrar() {
        instanceFactory::registerBlock(
            "twoClkIpSrc_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<twoClkIpSrc_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "twoClkIp");
    }
};
static _twoClkIpSrc_vl_registrar _twoClkIpSrc_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
