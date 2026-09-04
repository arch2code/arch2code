//

// GENERATED_CODE_PARAM --block=pySocket --parent=pySocket_tb
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "pySocket_hdl_sc_wrapper.h"
#include "VpySocket_hdl_sv_wrapper.h"

namespace {
struct _pySocket_vl_registrar {
    _pySocket_vl_registrar() {
        instanceFactory::registerBlock(
            "pySocket_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<pySocket_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "pySocket");
        instanceFactory::registerBlock(
            "pySocket_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<pySocket_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "pySocket");
    }
};
static _pySocket_vl_registrar _pySocket_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
