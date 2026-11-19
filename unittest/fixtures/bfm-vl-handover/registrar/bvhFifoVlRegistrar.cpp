//

// GENERATED_CODE_PARAM --block=bvhFifo --parent=bvhTop/../../yaml/bvh.yaml
// GENERATED_CODE_BEGIN --template=vlRegistrar
#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)
#include "instanceFactory.h"
#include "blockBase.h"
#include "bvhFifo_hdl_sc_wrapper.h"
#if defined(VERILATOR)
#include "VbvhFifo_hdl_sv_wrapper.h"
#elif defined(VCS_DUT)
#include "bvhFifo_hdl_sv_wrapper.h"
#else
#include "bvhFifo_hdl_sv_wrapper_xcelium.h"
#endif

namespace {
#if defined(VERILATOR)
using bvhFifo_hdl_sv_wrapper_dut_t = VbvhFifo_hdl_sv_wrapper;
#elif defined(VCS_DUT)
using bvhFifo_hdl_sv_wrapper_dut_t = bvhFifo_hdl_sv_wrapper;
#else
using bvhFifo_hdl_sv_wrapper_dut_t = bvhFifo_hdl_sv_wrapper;
#endif
struct _bvhFifo_vl_registrar {
    _bvhFifo_vl_registrar() {
        instanceFactory::registerBlock(
            "bvhFifo_verif",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<bvhFifo_hdl_sc_wrapper>(blockName, variant, bbMode));
            },
            "", "bfmVlHandover");
    }
};
static _bvhFifo_vl_registrar _bvhFifo_vl_registrar_instance;
} // namespace
#endif // VERILATOR || VCS_DUT || XCELIUM_DUT
// GENERATED_CODE_END
