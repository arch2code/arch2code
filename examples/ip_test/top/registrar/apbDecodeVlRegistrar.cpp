//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=apbDecode --parent=ip_top
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "apbDecode_hdl_sc_wrapper.h"
#include "VapbDecode_hdl_sv_wrapper.h"

namespace {
struct _apbDecode_vl_registrar {
    _apbDecode_vl_registrar() {
        instanceFactory::registerBlock(
            "apbDecode_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<apbDecode_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "ip_test");
        instanceFactory::registerBlock(
            "apbDecode_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<apbDecode_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "ip_test");
    }
};
static _apbDecode_vl_registrar _apbDecode_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
