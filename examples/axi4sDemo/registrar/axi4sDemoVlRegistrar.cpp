//

// GENERATED_CODE_PARAM --block=axi4sDemo --parent=axi4sDemo_tb
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "axi4sDemo_hdl_sc_wrapper.h"
#include "Vaxi4sDemo_hdl_sv_wrapper.h"

namespace {
struct _axi4sDemo_vl_registrar {
    _axi4sDemo_vl_registrar() {
        instanceFactory::registerBlock(
            "axi4sDemo_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<axi4sDemo_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "axi4sDemo");
    }
};
static _axi4sDemo_vl_registrar _axi4sDemo_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
