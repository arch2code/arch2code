
#ifndef IPLEAFVARIANTCONFIG_H_
#define IPLEAFVARIANTCONFIG_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --project=ip_test --context=../../leaf/yaml/ipLeaf.yaml
// GENERATED_CODE_BEGIN --template=config
#include <cstdint>
#include "clog2.h"

struct ipLeafDefaultConfig {
    static constexpr uint32_t LEAF_DATA_WIDTH = 4;
    static constexpr uint32_t LEAF_MEM_DEPTH = 4;
};

struct ipLeafVariantLeaf0Config {
    static constexpr uint32_t LEAF_DATA_WIDTH = 8;
    static constexpr uint32_t LEAF_MEM_DEPTH = 4;
};

// GENERATED_CODE_END

#endif //IPLEAFVARIANTCONFIG_H_
