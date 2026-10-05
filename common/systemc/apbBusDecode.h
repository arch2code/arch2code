#ifndef APBBUSDECODE_H
#define APBBUSDECODE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "apb_channel.h"
#include "logging.h"
#include <format>
#include <cmath>


// this template is for the demuxing of the apb bus to the correct block
// for firmware access to registers and memories
// the constructor should be called with an initializer list of the ports of the blocks that are to be connected to the bus
// in address order. If a block has multiple address spaces then the port should be provided multiple times
// numberOfaddressSpaces_ = the number of address spaces to be decoded
// addressShift_ = the number of bits to shift the address to the right to get the address space
template <class ADDR, class DATA>
class abpBusDecode
{
public:
    abpBusDecode(const uint32_t numberOfaddressSpaces_, const uint32_t addressShift_, sc_port<apb_in_if<ADDR, DATA>> &apbIn_,
                 const std::initializer_list<sc_port<apb_out_if<ADDR, DATA>>*>& ports)
        : apbIn(apbIn_),
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
            Q_ASSERT_CTX(false, apbIn.name(), std::format("abpBusDecode::abpBusDecode: number of ports {} does not match number of address spaces {}", blockPorts.size(), numberOfaddressSpaces));
        }
        uint32_t addressBits = 0;
        while ((1u << addressBits) < numberOfaddressSpaces) {
            addressBits++;
        }
        addressMask = (1u << addressBits) - 1;

    }
    void decodeThread(void)
    {
        while (true)
        {
            bool isWrite;
            ADDR addr;
            DATA data;
            apbIn->reqReceive(isWrite, addr, data);
            uint64_t address = addr._getAddress();
            uint32_t blockAddress = (address >> addressShift) & addressMask;
            if (blockAddress >= numberOfaddressSpaces)
            {
                Q_ASSERT_CTX(false, apbIn.name(), std::format("abpBusDecode::decodeThread: address {:x} out of range, block {:x}", address, blockAddress));
            }
            // blockPorts may hold fewer ports than there are address spaces
            auto port = blockAddress < blockPorts.size() ? blockPorts[blockAddress] : nullptr;
            if (port != nullptr)
            {
                if (isWrite)
                {
                    (*port)->request(isWrite, addr, data);
                } else {
                    (*port)->request(isWrite, addr, data);
                    apbIn->complete(data);
                }
            } else if (isWrite) {
                // An empty slot drops the write and reads 0xBADDC0DE, as the generated RTL does
                logging::GetInstance().logDirect(std::format("{}: firmware write to unmapped address 0x{:x} dropped",
                                                             apbIn.get_parent_object()->name(), address), LOG_ALWAYS);
            } else {
                logging::GetInstance().logDirect(std::format("{}: firmware read of unmapped address 0x{:x} returns 0xBADDC0DE",
                                                             apbIn.get_parent_object()->name(), address), LOG_ALWAYS);
                // truncated to a data bus narrower than 32 bits
                constexpr uint64_t dataMask = DATA::_bitWidth >= 32 ? 0xFFFFFFFFull : (1ull << DATA::_bitWidth) - 1;
                DATA badCode;
                badCode._setData(0xBADDC0DEull & dataMask);
                apbIn->complete(badCode);
            }
        }
    }

private:
    std::vector<sc_port<apb_out_if<ADDR, DATA>>*> blockPorts;
    sc_port<apb_in_if<ADDR, DATA>> &apbIn;
    uint32_t numberOfaddressSpaces;
    uint32_t addressShift;
    uint32_t addressMask;
};

#endif //APBBUSDECODE_H
