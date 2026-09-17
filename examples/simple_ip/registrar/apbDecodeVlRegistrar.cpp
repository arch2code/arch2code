//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=apbDecode --parent=simple_ip
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "apbDecode_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VapbDecode_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "apbDecode_hdl_sv_wrapper.h"
#else
#include "apbDecode_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using apbDecode_hdl_sv_wrapper_dut_t = VapbDecode_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using apbDecode_hdl_sv_wrapper_dut_t = apbDecode_hdl_sv_wrapper;
#else
using apbDecode_hdl_sv_wrapper_dut_t = apbDecode_hdl_sv_wrapper;
#endif
struct _apbDecode_vl_registrar {
    _apbDecode_vl_registrar() {
        instanceFactory::registerBlock(
            "apbDecode_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<apbDecode_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "simple_ip");
        instanceFactory::registerBlock(
            "apbDecode_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<apbDecode_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "simple_ip");
    }
};
static _apbDecode_vl_registrar _apbDecode_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
