// copyright contributors to arch2code project 2023
#ifndef MULTICYCLEBASE_H
#define MULTICYCLEBASE_H

#include <string>
#include <vector>
#include <memory>
#include "q_assert.h"
#include <list>

// interfaces and base functionality for processing buffer in multi cycle channels
// facade to remove complexity for interfaces that support multicycle usage
class multiCycleBase
{
public:
    multiCycleBase(std::string name, int burst_size)
     : m_name(name), m_burst_size(burst_size)  {}

    virtual ~multiCycleBase() {}

    // increment read and write cycle counters and return true if a new burst is starting
    virtual bool nextReadCycle(void)
    {
        m_read_cycles_current++;
        if (m_read_cycles_current == m_read_cycles_total)
        {
            m_read_cycles_current = 0;
            return true;
        }
        return false;
    }
    virtual bool nextWriteCycle(void)
    {
        m_write_cycles_current++;
        if (m_write_cycles_current == m_write_cycles_total)
        {
            m_write_cycles_current = 0;
            return true;
        }
        return false;
    }
    virtual bool isNewReadTransaction(void)
    {
        return (m_read_cycles_current == 0);
    }
    virtual bool isNewWriteTransaction(void)
    {
        return (m_write_cycles_current == 0);
    }
    virtual int getReadCycle(void) {return m_read_cycles_current;}
    virtual int getWriteCycle(void) {return m_write_cycles_current;}
    virtual void update(void) {}; // optional update function for derived class
    virtual void set_write_context(uint32_t context) {}; // allow for additional functionality if needed
    virtual int get_write_context(void) { return -1;}; // allow for additional functionality if needed
    virtual void push_context(uint32_t context)
    {
        list_mode = true; // we need to detect that this api was used, as it means the reader is transactional
        // if the writer is also transactional, we dont need to use the list at all as no one will be popping it
        // when A2C-154 is implemented we can simplify this
        if (!api_mode)
        {
            // TODO A2C-154 remove list_mode set
            transaction_context.push_back(context);
            Q_ASSERT(transaction_context.size() <= 2048, "transaction context list is too large"); // temp fix
        }
    }
    // the source will use additional field in send (write) api to provide context or length or tag for the transaction
    virtual void setSourceTransactional(void)
    {
        api_mode = true;
    }
    // the destination will provide length or tag for the transaction
    virtual void setDestinationTransactional(void)
    {
        list_mode = true;
    }

    // pure virtual functions to be implemented in derived class
    virtual uint8_t * getReadPtr(const int tag) = 0;
    virtual uint8_t * getWritePtr(const int tag) = 0;
    virtual uint32_t getReadBufferSize(const int tag) = 0; // override in derived class to return size of buffer
    virtual uint32_t getWriteBufferSize(const int tag) = 0;
    virtual void initRead(const int tag) = 0;
    virtual void copyReadData(const int tag, uint8_t *destination) = 0;
    virtual void initWrite(const int tag) = 0;
    virtual void copyWriteData(const int tag, uint8_t *source) = 0;

protected:
    std::string name() { return m_name; }
    std::string m_name = "";
    int m_burst_size = 0;
    int m_read_cycles_total = 0;
    int m_write_cycles_total = 0;
    int m_read_cycles_current = 0;
    int m_write_cycles_current = 0;
    bool api_mode = false; // indicates if the context is set in the src via api eg write(X, size_or_tag)
    bool list_mode = false; // indicates if the context is set in the dst via list eg push_context(X)
    std::list<uint32_t> transaction_context; // list of transaction sizes or tags
};

class multiCycleFactory
{
public:
    static std::unique_ptr<multiCycleBase> createMultiCycle(std::string name, std::string type, int burst_size, int size, std::string trackerName);
};

#endif // MULTICYCLEBASE_H
