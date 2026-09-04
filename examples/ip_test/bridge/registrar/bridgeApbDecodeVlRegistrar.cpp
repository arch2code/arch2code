//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=bridgeApbDecode --parent=ipBridge
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "bridgeApbDecode_hdl_sc_wrapper.h"
#include "VbridgeApbDecode_hdl_sv_wrapper.h"

namespace {
struct _bridgeApbDecode_vl_registrar {
    _bridgeApbDecode_vl_registrar() {
        instanceFactory::registerBlock(
            "bridgeApbDecode_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<bridgeApbDecode_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "ipBridge");
        instanceFactory::registerBlock(
            "bridgeApbDecode_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<bridgeApbDecode_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "ipBridge");
    }
};
static _bridgeApbDecode_vl_registrar _bridgeApbDecode_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
