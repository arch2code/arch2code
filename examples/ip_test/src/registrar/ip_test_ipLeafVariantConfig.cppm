//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipLeaf --parent=src/../../src/yaml/src.yaml
// GENERATED_CODE_BEGIN --template=config
module;
#include <cstdint>
#include "clog2.h"

export module ip_test.ipLeaf.config;

export struct ip_test_ipLeafDefaultConfig {
    static constexpr uint32_t LEAF_DATA_WIDTH = 4;
    static constexpr uint32_t LEAF_MEM_DEPTH = 4;
};

export struct ip_test_ipLeafVariantLeaf0Config {
    static constexpr uint32_t LEAF_DATA_WIDTH = 8;
    static constexpr uint32_t LEAF_MEM_DEPTH = 4;
};

// GENERATED_CODE_END
