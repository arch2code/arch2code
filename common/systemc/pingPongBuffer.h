// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef PINGPONGBUFFER_H
#define PINGPONGBUFFER_H

#include <string>
#include <vector>
#include <memory>
#include "q_assert.h"


class pingPongBuffer
{
public:
    pingPongBuffer(const std::string name_ = "", uint32_t pingpong_size_ = 0) :
        m_name(name_),
        m_pingpong_buffer_size_max(pingpong_size_),
        m_pingpong_buffer(2, std::vector<uint8_t>(pingpong_size_, 0))
    {
        m_pingpong_buffer_size[0] = pingpong_size_;
    }

    // for use cases where its not practical to declare the pingpong in the constructor
    // this is intended only to be used during initialization
    void alloc(int size)
    {
        m_pingpong_buffer_size_max = size;
        m_pingpong_buffer[0] = std::vector<uint8_t>(size);
        m_pingpong_buffer[1] = std::vector<uint8_t>(size);
        m_pingpong_buffer_size[0] = size;
    }
    // return getReadPtr based on current read buffer index
    inline uint8_t * getReadPtr()
    {
        return &m_pingpong_buffer[m_read_buffer_index][0];
    }

    // return getWritePtr based on current write buffer index
    inline uint8_t * getWritePtr()
    {
        return &m_pingpong_buffer[m_write_buffer_index][0];
    }

    // allow writer to override the default buffer size
    void setBufferSize(uint32_t size_)
    {
        Q_ASSERT_CTX(size_ <= m_pingpong_buffer_size_max, m_name, "Buffer size exceeds maximum");
        m_pingpong_buffer_size[m_write_buffer_index] = size_;
    }

    // get the read buffer size
    uint32_t getReadBufferSize(void)
    {
        return m_pingpong_buffer_size[m_read_buffer_index];
    }
    // get the write buffer size
    uint32_t getWriteBufferSize(void)
    {
        return m_pingpong_buffer_size[m_write_buffer_index];
    }
    // switch buffers
    void update(void)
    {
        m_read_buffer_index = m_write_buffer_index;
        m_write_buffer_index = (m_write_buffer_index + 1) & 1;
        m_pingpong_buffer_size[m_write_buffer_index] = m_pingpong_buffer_size_max;
    }

private:
    std::string m_name = "";
    int m_read_buffer_index = 0; // tracks current read buffer
    int m_write_buffer_index = 0; // tracks current write buffer
    uint32_t m_pingpong_buffer_size_max = 0;
    std::vector<std::vector<uint8_t> > m_pingpong_buffer; // actual buffer space
    uint32_t m_pingpong_buffer_size[2] = {0,0};

};

class multiCyclePingPong : public multiCycleBase
{
public:
    multiCyclePingPong(std::string name, int burst_size, int pingpong_size)
     :  multiCycleBase(name, burst_size),
        m_pingpong_buffer(name, pingpong_size+burst_size-1) // ensure we have enough space for the burst size
    {}
    // for ping pong implementation the tag is ignored
    uint8_t * getReadPtr(const int unused) override
    {
        return m_pingpong_buffer.getReadPtr();
    }
    uint8_t * getWritePtr(const int unused) override
    {
        return m_pingpong_buffer.getWritePtr();
    }
    // read buffer size, always comes from the pingpong buffer
    uint32_t getReadBufferSize(const int tag) override
    {
        return m_pingpong_buffer.getReadBufferSize();
    }
    // write buffer size, is either a constant from the pingpong buffer or a variable size for reader calling push_context
    uint32_t getWriteBufferSize(const int length) override
    {
        if (list_mode || api_mode)
        {
            return m_write_size;
        }
        return m_pingpong_buffer.getWriteBufferSize();
    }
    // for non-transactional access perform necessary initialization for read to make transactional
    void initRead(int length) override
    {
        // when the read is non-transactional, the size information is already in the pingpong buffer from the writer
        m_read_cycles_total = (m_pingpong_buffer.getReadBufferSize() + m_burst_size - 1) / m_burst_size; // round up
        m_read_cycles_current = 0;
    }
    // copy the segment of read data appropriate for the current cycle
    void copyReadData(const int length, uint8_t *destination) override
    {
        uint8_t *source = m_pingpong_buffer.getReadPtr();
        Q_ASSERT_CTX_NODUMP(source != nullptr, m_name, "source Null pointer in pingpong copyReadData");
        Q_ASSERT_CTX_NODUMP(destination != nullptr, m_name, "Destination Null pointer in pingpong copyReadData");
        memcpy(destination, source + (m_read_cycles_current * m_burst_size), m_burst_size);
    }
    void update(void) override
    {
        m_pingpong_buffer.update();
    }
    // perform necessary initialization for write
    void initWrite(int length) override
    {
        // note that list_mode and api_mode are not mutually exclusive as if both the reader and writer are transactional both will be true
        if (list_mode)
        {
            // in list use case we rely on the list of sizes created by the interface user on the read side for the write
            Q_ASSERT_CTX(transaction_context.size() > 0, m_name, "Write attempting to perform transaction without setting transaction size. Make sure the read code issues push_context() prior to writer writing");
            m_write_size = transaction_context.front();
            transaction_context.pop_front();
            m_pingpong_buffer.setBufferSize(m_write_size);
            Q_ASSERT_CTX(api_mode == false || m_write_size == length, m_name, "Read and write sources do not agree on the length of the transaction");
        }
        else if (api_mode)
        {
            // in value length mode we rely on the length information in the header/api which the caller provides
            m_write_size = length;
            m_pingpong_buffer.setBufferSize(m_write_size);
        }
        else
        {
            // fixed size transfer for every write
            m_write_size = m_pingpong_buffer.getWriteBufferSize();
        }
        m_write_cycles_total = (m_write_size + m_burst_size - 1) / m_burst_size; // round up
        m_write_cycles_current = 0;
    }
    // copy the segment of write data appropriate for the current cycle
    void copyWriteData(const int tag, uint8_t *source) override
    {
        uint8_t *destination = m_pingpong_buffer.getWritePtr();
        Q_ASSERT_CTX_NODUMP(source != nullptr, m_name, "source Null pointer in pingpong copyReadData");
        Q_ASSERT_CTX_NODUMP(destination != nullptr, m_name, "Destination Null pointer in pingpong copyReadData");
        memcpy(destination + (m_write_cycles_current * m_burst_size), source, m_burst_size);
    }
    void set_write_context(uint32_t size_) override
    {
        m_pingpong_buffer.setBufferSize(size_);
    }
    // this is an alias for setSourceTransactional for the case where we are using a pingpongbuffer with rdyVldBurst and the length is in the header
    // it ends up functionality equivalent to setSourceTransactional, but is more clear in the code
    void setHeaderMode(void)
    {
        setSourceTransactional();
    }
private:
    pingPongBuffer m_pingpong_buffer;
    int m_write_size = 0;
} ;




#endif // PINGPONGBUFFER_H
