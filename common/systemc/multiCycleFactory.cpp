#include "multiCycleBase.h"
#include "tracker.h"
#include "pingPongBuffer.h"
#include <cstring>
#include "q_assert.h"
#include <fmt/format.h>

std::unique_ptr<multiCycleBase> multiCycleFactory::createMultiCycle(std::string name, std::string type, int burst_size, int size, std::string trackerName)
{
    if (type == "fixed_size")
        return std::make_unique<multiCyclePingPong>(name, burst_size, size);
    else if (type == "header_tracker")
        return std::make_unique<multiCycleTracker>(burst_size, trackerName);
    else if (type == "header_size")
    {
        std::unique_ptr<multiCyclePingPong> temp = std::make_unique<multiCyclePingPong>(name, burst_size, size);
        temp->setHeaderMode();
        return temp;
    }
    else if (type == "api_list_tracker" )
        return std::make_unique<multiCycleTracker>(burst_size, trackerName);
    else if (type == "api_list_size" )
        return std::make_unique<multiCyclePingPong>(name, burst_size, size);
    else
    {
        Q_ASSERT_CTX(false, name, fmt::format("Multicycle type {} unknown", type));
        return nullptr;
    }
}
