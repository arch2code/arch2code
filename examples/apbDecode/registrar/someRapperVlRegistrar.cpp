//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=someRapper --parent=top
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "someRapper_hdl_sc_wrapper.h"
#include "VsomeRapper_hdl_sv_wrapper.h"

namespace {
struct _someRapper_vl_registrar {
    _someRapper_vl_registrar() {
        instanceFactory::registerBlock(
            "someRapper_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<someRapper_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "apbDecode");
    }
};
static _someRapper_vl_registrar _someRapper_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
