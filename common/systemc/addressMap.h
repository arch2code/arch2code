#ifndef ADDRESSMAP_H
#define ADDRESSMAP_H
#include <cstdint>
#include <string>
#include <memory>
#include "logging.h"
#include <format>
#include "apb_channel.h"
#include "addressBase.h"
#include "q_assert.h"


enum addressElementType {REG, MEM};

struct addressElement {
    addressElement(uint64_t _address, uint64_t _size, addressElementType _type,std::string _name, addressBase *_ptr) :
        m_address(_address), m_size(_size), m_type(_type), m_name(_name), m_ptr(_ptr) {}
    uint64_t m_address;
    uint64_t m_size;
    addressElementType m_type;
    std::string m_name;
    addressBase *m_ptr;
};

class addressMap
{
public:
    addressMap(logBlock &log) : log_(log)  {}
    uint64_t getLastWriteAddress(void)
    {
        return m_lastWriteAddress;
    }
    void addRegister(uint64_t address, uint64_t size, std::string name, addressBase *ptr)
    {
        Q_ASSERT_CTX(m_addressMap.size()==0 || (address >= m_addressMap.back().m_address + m_addressMap.back().m_size), name, "Address overlap");
        m_addressMap.emplace_back(addressElement(address, size, addressElementType::REG, name, ptr));
    }
    void addMemory(uint64_t address, uint64_t size, std::string name, addressBase *ptr)
    {
        Q_ASSERT_CTX(m_addressMap.size()==0 || (address >= m_addressMap.back().m_address + m_addressMap.back().m_size), name, "Address overlap");
        m_addressMap.emplace_back(addressElement(address, size, addressElementType::MEM, name, ptr));
    }
    void cpu_write(uint64_t address, uint32_t val) {
        m_lastWriteAddress = address;
        auto it = find(address);
        if (it->m_type == addressElementType::REG) {
            log_.logPrint([&]() { return std::format("Reg {} Write Addr:0x{:x} Val:0x{:x}", it->m_name, address, val); });
        } else {
            log_.logPrint([&]() { return std::format("Mem {} Write Addr:0x{:x} Val:0x{:x}", it->m_name, address, val); });
        }
        it->m_ptr->cpu_write((address - it->m_address), val);
    }
    uint32_t cpu_read(uint64_t address) {
        auto it = find(address);
        uint32_t val = it->m_ptr->cpu_read((address - it->m_address));
        if (it->m_type == addressElementType::REG) {
            log_.logPrint([&]() { return std::format("Reg {} Read Addr:0x{:x} Val:0x{:x}", it->m_name, address, val); });
        } else {
            log_.logPrint([&]() { return std::format("Mem {} Read Addr:0x{:x} Val:0x{:x}", it->m_name, address, val); });
        }
        return val;
    }
    // linear search for now
    addressElement *find(uint64_t address) {
        for (auto &it : m_addressMap)
        {
            if (address >= it.m_address && address < it.m_address + it.m_size)
            {
                return &it;
            }
        }
        Q_ASSERT_CTX(false, "", std::format("Invalid address 0x{:x}", address));
        return nullptr;
    }
private:
    std::vector<addressElement> m_addressMap;
    uint64_t m_lastWriteAddress=0;
    logBlock &log_;  // parents logging reference
};


template <class ADDR, class DATA>
void registerHandler(addressMap &regs, apb_in< ADDR, DATA > &apbIn, uint64_t addressMask)
{
    ADDR addr;
    DATA data;
    bool isWrite;
    while(true)
    {
        apbIn->reqReceive(isWrite, addr, data);
        uint64_t address = addr._getAddress() & (addressMask);
        if (isWrite)
        {
            regs.cpu_write(address, data._getData());
        } else {
            data._setData(regs.cpu_read(address));
            apbIn->complete(data);
        }
    }
}

#endif //(ADDRESSMAP_H)
