//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=dataGen --parent=simple_ip
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "dataGen_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VdataGen_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "dataGen_hdl_sv_wrapper.h"
#else
#include "dataGen_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using dataGen_hdl_sv_wrapper_dut_t = VdataGen_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using dataGen_hdl_sv_wrapper_dut_t = dataGen_hdl_sv_wrapper;
#else
using dataGen_hdl_sv_wrapper_dut_t = dataGen_hdl_sv_wrapper;
#endif
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
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
