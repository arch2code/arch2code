//

// GENERATED_CODE_PARAM --block=hierVlDemo --parent=hierVlDemo_tb
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "hierVlDemo_hdl_sc_wrapper.h"
#include "VhierVlDemo_hdl_sv_wrapper.h"

namespace {
struct _hierVlDemo_vl_registrar {
    _hierVlDemo_vl_registrar() {
        instanceFactory::registerBlock(
            "hierVlDemo_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<hierVlDemo_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "hierVlDemo");
    }
};
static _hierVlDemo_vl_registrar _hierVlDemo_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
