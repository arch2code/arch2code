//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockA --parent=mixed
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "blockA_hdl_sc_wrapper.h"
#include "VblockA_hdl_sv_wrapper.h"

namespace {
struct _blockA_vl_registrar {
    _blockA_vl_registrar() {
        instanceFactory::registerBlock(
            "blockA_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockA_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "mixed");
        instanceFactory::registerBlock(
            "blockA_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockA_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "mixed");
    }
};
static _blockA_vl_registrar _blockA_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
