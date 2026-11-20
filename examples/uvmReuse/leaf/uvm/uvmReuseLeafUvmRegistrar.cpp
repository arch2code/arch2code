// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseLeaf
// GENERATED_CODE_BEGIN --template=uvmRegistrar
#if defined(XCELIUM) || defined(VCS)
#include "instanceFactory.h"
#include "blockBase.h"
#include "uvmReuseLeaf_uvm_sc_wrapper.h"
#if defined(XCELIUM)
#include "uvmReuseLeaf_w4_uvm_tb_xcelium.h"
#include "uvmReuseLeaf_w8_uvm_tb_xcelium.h"
#else
// Written by vlogan -sc_model from the port map.
#include "uvmReuseLeaf_w4_uvm_tb.h"
#include "uvmReuseLeaf_w8_uvm_tb.h"
#endif

namespace {
struct _uvmReuseLeaf_uvm_registrar {
    _uvmReuseLeaf_uvm_registrar() {
        instanceFactory::registerBlock(
            "uvmReuseLeaf_uvm",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseLeaf_uvm_sc_wrapper<uvmReuseLeaf_w4_uvm_tb, uvmReuseLeafW4Config>>(blockName, variant, bbMode));
            },
            "w4", "uvmReuseLeaf");
        instanceFactory::registerBlock(
            "uvmReuseLeaf_uvm",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseLeaf_uvm_sc_wrapper<uvmReuseLeaf_w8_uvm_tb, uvmReuseLeafW8Config>>(blockName, variant, bbMode));
            },
            "w8", "uvmReuseLeaf");
    }
};
static _uvmReuseLeaf_uvm_registrar _uvmReuseLeaf_uvm_registrar_instance;
} // namespace
#endif // XCELIUM || VCS

// GENERATED_CODE_END
