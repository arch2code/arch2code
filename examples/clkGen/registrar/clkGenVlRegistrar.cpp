//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=clkGen --parent=clkGen_tb
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "clkGen_hdl_sc_wrapper.h"
#include "VclkGen_hdl_sv_wrapper.h"

namespace {
struct _clkGen_vl_registrar {
    _clkGen_vl_registrar() {
        instanceFactory::registerBlock(
            "clkGen_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<clkGen_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "clkGen");
    }
};
static _clkGen_vl_registrar _clkGen_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
