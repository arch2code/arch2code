
#ifndef IPLEAFCONFIG_H_CONFIG_H
#define IPLEAFCONFIG_H_CONFIG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include <cstdint>

// GENERATED_CODE_PARAM --context=ipLeaf.yaml
// GENERATED_CODE_BEGIN --template=includes --section=config
struct ipLeafDefaultConfig {
    static constexpr uint32_t LEAF_DATA_WIDTH = 4;
    static constexpr uint32_t LEAF_MEM_DEPTH = 4;
};

struct ipLeafVariantLeaf0Config {
    static constexpr uint32_t LEAF_DATA_WIDTH = 4;
    static constexpr uint32_t LEAF_MEM_DEPTH = 4;
};

// GENERATED_CODE_END

#endif //IPLEAFCONFIG_H_CONFIG_H
