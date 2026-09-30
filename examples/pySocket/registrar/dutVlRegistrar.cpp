//

// GENERATED_CODE_PARAM --block=dut --parent=pySocket_tb
// GENERATED_CODE_BEGIN --template=vlRegistrar
#ifdef VERILATOR
#include "instanceFactory.h"
#include "blockBase.h"
#include "dut_hdl_sc_wrapper.h"
#include "Vdut_hdl_sv_wrapper.h"

namespace {
struct _dut_vl_registrar {
    _dut_vl_registrar() {
        instanceFactory::registerBlock(
            "dut_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<dut_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "pySocket");
        instanceFactory::registerBlock(
            "dut_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<dut_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "pySocket");
    }
};
static _dut_vl_registrar _dut_vl_registrar_instance;
} // namespace
#endif // VERILATOR
// GENERATED_CODE_END
