//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=tbPeer --parent=xif_tb/xif.yaml
// GENERATED_CODE_BEGIN --template=config
module;
#include <cstdint>
#include "clog2.h"

export module xif.tbPeer.config;

export struct xif_tbPeerDefaultConfig {
    static constexpr uint32_t DATA_WIDTH = 16;
    static constexpr uint32_t FRAME_HEIGHT = 8;
    static constexpr uint32_t FRAME_WIDTH = 8;
};

export struct xif_tbPeerPv0Config {
    static constexpr uint32_t DATA_WIDTH = 16;
    static constexpr uint32_t FRAME_HEIGHT = 12;
    static constexpr uint32_t FRAME_WIDTH = 12;
};

export template<typename ContainerConfig>
struct xif_tbPeerPvSourcedConfig {
    static constexpr uint32_t DATA_WIDTH = ContainerConfig::DATA_WIDTH;
    static constexpr uint32_t FRAME_HEIGHT = ContainerConfig::FRAME_HEIGHT;
    static constexpr uint32_t FRAME_WIDTH = ContainerConfig::FRAME_WIDTH;
};

// GENERATED_CODE_END
