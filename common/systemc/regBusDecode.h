#ifndef REGBUSDECODE_H
#define REGBUSDECODE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "logging.h"
#include <format>
#include <cmath>


// this template is for the demuxing of a register bus to the correct block
// for firmware access to registers and memories. IN_IF and OUT_IF are the bus
// protocol's completer and requester interfaces: IN_IF provides reqReceive,
// complete and receivedWantsResponse, OUT_IF provides request and
// requestWithResponse.
// the constructor should be called with an initializer list of the ports of the blocks that are to be connected to the bus
// in address order. If a block has multiple address spaces then the port should be provided multiple times
// numberOfaddressSpaces_ = the number of address spaces to be decoded
// addressShift_ = the number of bits to shift the address to the right to get the address space
template <class ADDR, class DATA, template <class, class> class IN_IF, template <class, class> class OUT_IF>
class regBusDecode
{
public:
    regBusDecode(const uint32_t numberOfaddressSpaces_, const uint32_t addressShift_, sc_port<IN_IF<ADDR, DATA>> &busIn_,
                 const std::initializer_list<sc_port<OUT_IF<ADDR, DATA>>*>& ports)
        : busIn(busIn_),
        numberOfaddressSpaces(numberOfaddressSpaces_),
        addressShift(addressShift_)
    {
        for (auto port : ports) {
            // Process each port in the initializer list as needed
            // For example, you can store them in a vector or perform some other operations.
            blockPorts.push_back(port);
        }
        if (blockPorts.size() > numberOfaddressSpaces)
        {
            Q_ASSERT_CTX(false, busIn.name(), std::format("regBusDecode::regBusDecode: number of ports {} does not match number of address spaces {}", blockPorts.size(), numberOfaddressSpaces));
        }
        uint32_t addressBits = 0;
        while ((1u << addressBits) < numberOfaddressSpaces) {
            addressBits++;
        }
        addressMask = (1u << addressBits) - 1;

    }
    // errorResponses: an access to an empty address space completes with the bus error response
    void decodeThread(bool errorResponses = false)
    {
        while (true)
        {
            bool isWrite;
            ADDR addr;
            DATA data;
            busIn->reqReceive(isWrite, addr, data);
            uint64_t address = addr._getAddress();
            uint32_t blockAddress = (address >> addressShift) & addressMask;
            if (blockAddress >= numberOfaddressSpaces)
            {
                Q_ASSERT_CTX(false, busIn.name(), std::format("regBusDecode::decodeThread: address {:x} out of range, block {:x}", address, blockAddress));
            }
            // blockPorts may hold fewer ports than there are address spaces
            auto port = blockAddress < blockPorts.size() ? blockPorts[blockAddress] : nullptr;
            if (port != nullptr)
            {
                // Forward in the mode received: a posted write stays posted,
                // and only a response-aware request waits for the error response.
                if (busIn->receivedWantsResponse())
                {
                    const bool slverr = (*port)->requestWithResponse(isWrite, addr, data);
                    busIn->complete(data, slverr);
                } else {
                    (*port)->request(isWrite, addr, data);
                    if (!isWrite) {
                        busIn->complete(data);
                    }
                }
            } else if (isWrite) {
                // An empty slot drops the write and reads 0xBADDC0DE, as the generated RTL does
                logging::GetInstance().logDirect(std::format("{}: firmware write to unmapped address 0x{:x} dropped",
                                                             busIn.get_parent_object()->name(), address), LOG_ALWAYS);
                busIn->complete(data, errorResponses);
            } else {
                logging::GetInstance().logDirect(std::format("{}: firmware read of unmapped address 0x{:x} returns 0xBADDC0DE",
                                                             busIn.get_parent_object()->name(), address), LOG_ALWAYS);
                // truncated to a data bus narrower than 32 bits
                constexpr uint64_t dataMask = DATA::_bitWidth >= 32 ? 0xFFFFFFFFull : (1ull << DATA::_bitWidth) - 1;
                DATA badCode;
                badCode._setData(0xBADDC0DEull & dataMask);
                busIn->complete(badCode, errorResponses);
            }
        }
    }

private:
    std::vector<sc_port<OUT_IF<ADDR, DATA>>*> blockPorts;
    sc_port<IN_IF<ADDR, DATA>> &busIn;
    uint32_t numberOfaddressSpaces;
    uint32_t addressShift;
    uint32_t addressMask;
};

#endif //REGBUSDECODE_H
