#ifndef HWMEMORY_H
#define HWMEMORY_H
#include <cstdint>
#include <string>
#include <memory>
#include <format>
#include "addressBase.h"
#include "timedDelay.h"
#include "synchLock.h"

#include "memory_channel.h"
#include <systemc>

// A:64 D:32 CPU Register access bus
// N : size of CPU D-Bus aligned data entry, in bytes


class memBase : public addressBase
{
public:
    memBase() {};
    virtual void setTimed(uint64_t nsec, timedDelayMode mode) = 0;
    virtual void cpu_write(uint64_t address, uint32_t val) = 0;  //virtual methods to be overridden in template
    virtual uint32_t cpu_read(uint64_t address) = 0;
private:

};


class memories
{
public:
    memories() {};
    void addMemory(memBase *mem, std::string name)
    {
        m_memories[name] = mem;
    }
    memBase *getMemory(std::string name)
    {
        return m_memories[name];
    }
    void setTimed(int nsec, timedDelayMode mode)
    {
        for (auto &it : m_memories)
        {
            it.second->setTimed(nsec, mode);
        }
    }

private:
    std::map<std::string, memBase*> m_memories;
};

enum hwMemoryType {HWMEMORYTYPE_NORMAL, HWMEMORYTYPE_LOCAL};
// What firmware may do to a memory through cpu_read/cpu_write. A firmware
// access the mode forbids is no bus error: a write is dropped and a read
// returns 0, each logged.
enum hwMemoryFwAccess {HWMEMORYFWACCESS_RW, HWMEMORYFWACCESS_RO, HWMEMORYFWACCESS_WO};
// ROW_BYTES is the address stride between rows, a power of 2 of at least 4.
// It is the address map's row footprint, which for a parameterizable structure
// is sized for the widest variant. Bytes of a row past the structure's width
// read 0 and drop writes.
template <class MEM_DATA, int ROW_BYTES = nextPowerOf2min4(MEM_DATA::_byteWidth)>
class hwMemory : public memBase
{
    static_assert(ROW_BYTES >= nextPowerOf2min4(MEM_DATA::_byteWidth) && (ROW_BYTES & (ROW_BYTES - 1)) == 0,
                  "ROW_BYTES must be a power of 2 that holds a whole row");
public:
    hwMemory(const char * hierarchicalName_, const char * memName_, memories &memories_, uint64_t rows_, hwMemoryType memType_ = HWMEMORYTYPE_NORMAL,
             hwMemoryFwAccess fwAccess_ = HWMEMORYFWACCESS_RW)
        : m_mem(rows_),
            rows(rows_),
            m_name(std::string(hierarchicalName_) + "_" + std::string(memName_)),
            m_memName(memName_),
            m_delay(m_name),
            m_memType(memType_),
            m_fwAccess(fwAccess_)
    {
        memories_.addMemory(this, m_name);
    }
    void cpu_write(uint64_t address, uint32_t val) override {
        uint32_t index = address/_size();
        Q_ASSERT(index < rows, "Address out of range");
        if (m_fwAccess == HWMEMORYFWACCESS_RO) {
            logging::GetInstance().logDirect(std::format("{}: firmware write to read-only memory at offset 0x{:x} dropped", m_name, address), LOG_ALWAYS);
            return;
        }
        uint32_t n = address%_size();
        m_val_sc = m_mem[index].sc_pack();
        m_val_sc.range(8*n+31, 8*n) = val;
        m_mem[index].sc_unpack(m_val_sc);
    }
    uint32_t cpu_read(uint64_t address) override {
        uint32_t index = address/_size();
        Q_ASSERT(index < rows, "Address out of range");
        if (m_fwAccess == HWMEMORYFWACCESS_WO) {
            logging::GetInstance().logDirect(std::format("{}: firmware read of write-only memory at offset 0x{:x} returns 0", m_name, address), LOG_ALWAYS);
            return 0;
        }
        uint32_t n = address%_size();
        m_val_sc = m_mem[index].sc_pack();
        return (uint32_t) m_val_sc.range(8*n+31, 8*n).to_uint64();
    }
    constexpr int _size(void) {
        return ROW_BYTES;
    }
    // direct access for compatability and backdoor uses such as logging
    MEM_DATA& operator[] (uint64_t index) {
        Q_ASSERT(index < rows, "Address out of range");
        return m_mem[index];
    }
    // timed access without any locking
    MEM_DATA read(uint64_t index) {
        Q_ASSERT(index < rows, "Address out of range");
        MEM_DATA val;
        if (m_memType == HWMEMORYTYPE_NORMAL) {
            m_delay.delay();
        }
        val = m_mem[index];
        return val;
    }
    // timed access without any locking
    void write(uint64_t index, MEM_DATA val) {
        Q_ASSERT(index < rows, "Address out of range");
        Q_ASSERT(m_memType == HWMEMORYTYPE_NORMAL, "write called on register memory - not allowed");
        m_delay.delay(); m_mem[index] = val;
    }
    // for use in datapath memories
    void writeNoDelay(uint64_t index, MEM_DATA val) {
        Q_ASSERT(index < rows, "Address out of range");
        Q_ASSERT(m_memType == HWMEMORYTYPE_NORMAL, "write called on register memory - not allowed");
        m_mem[index] = val;
    }
    // program the timing access parameters
    void setTimed(uint64_t nsec, timedDelayMode mode) override
    {
        m_delay.setTimed(nsec, mode);
    }
    // read-modify-write access with locking. This function will create a row lock on the memory as part of the read
    // the magicNumber is used to distinguish between different thread accesses to the same row
    // this is used for synchLock synchronization (a2c-pro feature)in tandem mode
    MEM_DATA readRMW(uint64_t index, uint64_t magicNumber) {
        Q_ASSERT(m_synch, "writeRMW called on non-synch memory");
        Q_ASSERT(m_rowLock != nullptr, "missing call to configureSynch")
        Q_ASSERT(index < rows, "Address out of range");
        Q_ASSERT(m_memType == HWMEMORYTYPE_NORMAL, "readRMW called on register memory - not allowed");
        MEM_DATA val;
        m_delay.delay();
        m_rowLock->lock(index, magicNumber);
        val = m_mem[index];
        return val;
    }
    void lock(uint64_t index, uint64_t magicNumber) {
        Q_ASSERT(m_synch, "lock called on non-synch memory");
        Q_ASSERT(m_rowLock != nullptr, "missing call to configureSynch")
        Q_ASSERT(index < rows, "Address out of range");
        Q_ASSERT(m_memType == HWMEMORYTYPE_NORMAL, "readRMW called on register memory - not allowed");
        m_rowLock->lock(index, magicNumber);
    }
    // read-modify-write access with locking. This function will release the lock created with the readRMW function
    void writeRMW(uint64_t index, MEM_DATA val) {
        Q_ASSERT(m_synch, "writeRMW called on non-synch memory");
        Q_ASSERT(index < rows, "Address out of range");
        Q_ASSERT(m_memType == HWMEMORYTYPE_NORMAL, "writeRMW called on register memory - not allowed");
        m_delay.delay();
        m_mem[index] = val;
        m_rowLock->unlock(index);
    }
    // release the lock created with the readRMW function without any write
    void releaseRMW(uint64_t index) {
        Q_ASSERT(m_synch, "releaseRMW called on non-synch memory");
        Q_ASSERT(index < rows, "Address out of range");
        Q_ASSERT(m_memType == HWMEMORYTYPE_NORMAL, "releaseRMW called on register memory - not allowed");
        m_rowLock->unlock(index);
    }

    MEM_DATA * data(void) {
        return m_mem.data();
    }
    std::string name(void) {
        return m_name;
    }
    // sets up the memory for row synchronization
    void configureSynch(std::string synchLockNameBase, std::function<std::string(const arraySynchRecord &value)> prt)
    {
        m_synch = true;
        m_rowLock = std::make_unique<synchArrayLock>(synchLockNameBase, m_memName, rows, prt);
        logging::GetInstance().registerStatus(m_name, [this](){statusPrint();});

    }
    void statusPrint(void) {
        if (!m_synch) return;
        logging &lg = logging::GetInstance();
        for (uint64_t i = 0; i < rows; i++) {
            if (m_rowLock->isLocked(i)) {
                std::stringstream ss;
                ss << m_name<< "[" << std::hex << i << "] locked:" << m_mem[i].prt() << '\n';
                lg.logDirect(ss.str(), LOG_IMPORTANT);
            }
        }
    }

    // Binds a channel (passed by reference) to a new service thread
    template <class ADDR>
    void bindPort(memory_in_if<ADDR, MEM_DATA>& port) {
        // sc_bind creates a callback to serviceThread, passing '&port' as the argument.
        // sc_spawn creates a new SystemC process to run that callback.
        sc_core::sc_spawn(sc_core::sc_bind(&hwMemory::serviceThread<ADDR>, this, &port));
    }

    // The thread loop that services the specific channel
    template <class ADDR>
    void serviceThread(memory_in_if<ADDR, MEM_DATA>* port) {
        bool isWrite;
        ADDR addrStruct;
        MEM_DATA data;
        while(true) {
             // Wait for a request on this channel
             port->reqReceive(isWrite, addrStruct, data);
             
             // Process request
             uint64_t addrVal = addrStruct._getAddress();
             if (isWrite) {
                 write(addrVal, data);
             } else {
                 data = read(addrVal);
                // Send completion/data back
                port->complete(data);
             }
             
        }
    }

private:
    std::vector<MEM_DATA> m_mem;
    uint64_t rows;
    sc_bv<ROW_BYTES * 8> m_val_sc;
    std::string m_name = "";
    std::string m_memName = "";
    timedDelay m_delay;
    bool m_synch = false;
    std::unique_ptr<synchArrayLock> m_rowLock;
    hwMemoryType m_memType;
    hwMemoryFwAccess m_fwAccess;
};

// ROW_BYTES is the address stride between rows, as for hwMemory.
template <class ADDR, class DATA, int ROW_BYTES = nextPowerOf2min4(DATA::_byteWidth)>
class hwMemoryPort : public memBase
{
    static_assert(ROW_BYTES >= nextPowerOf2min4(DATA::_byteWidth) && (ROW_BYTES & (ROW_BYTES - 1)) == 0,
                  "ROW_BYTES must be a power of 2 that holds a whole row");
public:
    // name is logged when the mode drops an access, so it is required for ro and wo.
    hwMemoryPort(memory_out<ADDR, DATA> &port, hwMemoryFwAccess fwAccess_ = HWMEMORYFWACCESS_RW, std::string name_ = "")
        : m_port(port), m_fwAccess(fwAccess_), m_name(name_) {}

    void cpu_write(uint64_t address, uint32_t val) override {
        if (m_fwAccess == HWMEMORYFWACCESS_RO) {
            logging::GetInstance().logDirect(std::format("{}: firmware write to read-only memory at offset 0x{:x} dropped", m_name, address), LOG_ALWAYS);
            return;
        }
        uint32_t index = address/_size();
        uint32_t n = address%_size();
        ADDR addr_obj;
        addr_obj.unpack((typename ADDR::_packedSt)index);
        DATA data_obj;

        // RMW
        m_port->request(false, addr_obj, data_obj);

        m_val_sc = data_obj.sc_pack();
        m_val_sc.range(8*n+31, 8*n) = val;
        data_obj.sc_unpack(m_val_sc);
        
        m_port->request(true, addr_obj, data_obj);
    }
    uint32_t cpu_read(uint64_t address) override {
        if (m_fwAccess == HWMEMORYFWACCESS_WO) {
            logging::GetInstance().logDirect(std::format("{}: firmware read of write-only memory at offset 0x{:x} returns 0", m_name, address), LOG_ALWAYS);
            return 0;
        }
        uint32_t index = address/_size();
        uint32_t n = address%_size();
        ADDR addr_obj;
        addr_obj.unpack((typename ADDR::_packedSt)index);
        DATA data_obj;

        m_port->request(false, addr_obj, data_obj);
        
        m_val_sc = data_obj.sc_pack();
        return (uint32_t) m_val_sc.range(8*n+31, 8*n).to_uint64();
    }
    
    constexpr int _size(void) {
        return ROW_BYTES;
    }

    void setTimed(uint64_t nsec, timedDelayMode mode) override
    {
    }

private:
    memory_out<ADDR, DATA> &m_port;
    sc_bv<ROW_BYTES * 8> m_val_sc;
    hwMemoryFwAccess m_fwAccess;
    std::string m_name;
};

#endif //(HWMEMORY_H)
