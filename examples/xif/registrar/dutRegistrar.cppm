//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=dut --parent=xif_tb
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"
#include "xifVariantConfig.h"

export module xif.xif_dut.registrar;
import xif_dut.block;

namespace {
struct _dut_registrar {
    _dut_registrar() {
        instanceFactory::registerBlock(
            "dut_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<dut<dutDutV0Config>>(blockName, variant, bbMode));
            },
            "dutV0", "xif");
        instanceFactory::registerBlock(
            "dut_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<dut<dutDutV0Config>>(blockName, variant, bbMode));
            },
            "dutV0", "xif.xif_tb.xif_dut");
    }
};
static _dut_registrar _dut_registrar_instance;
} // namespace
// GENERATED_CODE_END
