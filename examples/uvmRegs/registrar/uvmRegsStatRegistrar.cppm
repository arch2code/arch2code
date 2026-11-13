//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsStat --parent=uvmRegs/../../yaml/uvmRegs.yaml
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module uvmRegs.uvmRegs_uvmRegsStat.registrar;
import uvmRegs_uvmRegsStat.block;
import uvmRegs.uvmRegsStat.config;

namespace {
struct _uvmRegsStat_registrar {
    _uvmRegsStat_registrar() {
        instanceFactory::registerBlock(
            "uvmRegsStat_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmRegsStat<uvmRegs_uvmRegsStatV0Config>>(blockName, variant, bbMode));
            },
            "v0", "uvmRegs");
        instanceFactory::registerBlock(
            "uvmRegsStat_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmRegsStat<uvmRegs_uvmRegsStatV0Config>>(blockName, variant, bbMode));
            },
            "v0", "uvmRegs.uvmRegs.uvmRegs_uvmRegsStat");
    }
};
static _uvmRegsStat_registrar _uvmRegsStat_registrar_instance;
} // namespace
// GENERATED_CODE_END
