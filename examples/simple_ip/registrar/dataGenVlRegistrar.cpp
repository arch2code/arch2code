//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=dataGen --parent=simple_ip
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "dataGen_hdl_sc_wrapper.h"
#include "VdataGen_hdl_sv_wrapper.h"

namespace {
struct _dataGen_vl_registrar {
    _dataGen_vl_registrar() {
        instanceFactory::registerBlock(
            "dataGen_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<dataGen_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "simple_ip");
        instanceFactory::registerBlock(
            "dataGen_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<dataGen_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "simple_ip");
    }
};
static _dataGen_vl_registrar _dataGen_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
