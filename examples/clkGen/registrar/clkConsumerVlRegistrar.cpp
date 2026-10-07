//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=clkConsumer --parent=clkGen
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "clkConsumer_hdl_sc_wrapper.h"
#include "VclkConsumer_hdl_sv_wrapper.h"

namespace {
struct _clkConsumer_vl_registrar {
    _clkConsumer_vl_registrar() {
        instanceFactory::registerBlock(
            "clkConsumer_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<clkConsumer_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "clkGen");
    }
};
static _clkConsumer_vl_registrar _clkConsumer_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
