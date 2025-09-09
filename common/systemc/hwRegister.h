#ifndef HWREGISTER_H
#define HWREGISTER_H
#include <cstdint>

#include "asyncEvent.h"
#include "addressBase.h"

// A:64 D:32 CPU Register access bus
// N : size of CPU D-Bus aligned data entry, in bytes

class regBase : public addressBase
{
public:
    regBase() {};
    virtual void cpu_write(uint64_t address, uint32_t val) = 0;  //virtual methods to be overridden in template
    virtual uint32_t cpu_read(uint64_t address) = 0;
private:
};

template <class REG_DATA, int N=4>
class hwRegister : public regBase
{
public:
    hwRegister()
    {
        memset(&m_val, 0, sizeof(m_val));
    }
    uint32_t cpu_read(uint64_t address) override
    {
        Q_ASSERT_CTX(address < N, "", "Address out of range");
        uint32_t val;
        m_val_sc = m_val.sc_pack();
        val = (uint32_t) m_val_sc.range(8*address+31, 8*address).to_uint64();
        return val;
    }
    void cpu_write(uint64_t address, uint32_t val) override
    {
        Q_ASSERT_CTX(address < N, "", "Address out of range");
        m_val_sc = m_val.sc_pack();
        m_val_sc.range(8*address+31, 8*address) = val;
        m_val.sc_unpack(m_val_sc);
        if (m_event != nullptr && address == (N-4))
        {
            m_event->notify();
        }
    }
    REG_DATA read(void)
    {
        return m_val;
    }
    void write(REG_DATA val)
    {
        m_val = val;
        if (m_event != nullptr)
        {
            m_event->notify();
        }
    }
    void copy(REG_DATA& to)
    {
        to = *this;
    }
    void registerEvent(sc_event *event)
    {
        m_event = event;
    }
    REG_DATA m_val;
    sc_event *m_event=nullptr;
private:
    sc_bv<N*8> m_val_sc;
};

template <class REG_DATA, class PORT, int N, bool RO>
class hwRegisterIf : public regBase
{
public:
    hwRegisterIf(PORT *port_) : m_port(port_)
    {
       memset(&m_val, 0, sizeof(m_val));
    }
    uint32_t cpu_read(uint64_t address) override
    {
        Q_ASSERT_CTX(address < N, "", "Address out of range");
        uint32_t val;
        m_val_sc = m_val.sc_pack();
        val = (uint32_t) m_val_sc.range(8*address+31, 8*address).to_uint64();
        return val;
    }
    void cpu_write(uint64_t address, uint32_t val) override
    {
        if constexpr (RO)
        {
            Q_ASSERT_CTX(false, "", "Attempt to write to read-only register");
        } else {
            Q_ASSERT_CTX(address < N, "", "Address out of range");
            m_val_sc = m_val.sc_pack();
            m_val_sc.range(8*address+31, 8*address) = val;
            m_val.sc_unpack(m_val_sc);
            if (address == (N-4))
            {
                (*m_port)->write(m_val);
            }
        }
    }
    REG_DATA read(void)
    {
        return m_val;
    }
    void write(REG_DATA val)
    {
        if constexpr (RO)
        {
            Q_ASSERT_CTX(false, "", "Attempt to write to read-only register");
        } else {
            m_val = val;
            (*m_port)->write(m_val);
        }
    }
    void copy(REG_DATA& to)
    {
        to = *this;
    }
    REG_DATA m_val;
private:
    sc_bv<N*8> m_val_sc;
    PORT *m_port;
};

#endif //(HWREGISTER_H)
