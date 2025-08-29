// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef MEMORY_CHANNEL_H
#define MEMORY_CHANNEL_H

#include "sysc/communication/sc_communication_ids.h"
#include "sysc/communication/sc_prim_channel.h"
#include "sysc/communication/sc_interface.h"
#include "sysc/kernel/sc_event.h"
#include "sysc/kernel/sc_simcontext.h"
#include "sysc/tracing/sc_trace.h"
#include <typeinfo>
#include <iostream>
#include "interfaceBase.h"
#include "trackerBase.h"
#include "portBase.h"

namespace sc_core {

// ----------------------------------------------------------------------------
//  CLASS : memory_in_if<A, D>
// ----------------------------------------------------------------------------

template <class A, class D>
class memory_in_if
: virtual public sc_interface, virtual public portBase
{
public:

    // blocking read/write
    virtual void reqReceive(bool &isWrite, A&, D& ) = 0;
    virtual void complete(const D&) = 0; // completion only on read

protected:
    // constructor
    memory_in_if() {}

private:
    // disabled
    memory_in_if( const memory_in_if<A, D>& );
    memory_in_if<A, D>& operator = ( const memory_in_if<A, D>& );
};

// ----------------------------------------------------------------------------
//  CLASS : memory_out_if<A, D>
// ----------------------------------------------------------------------------

template <class A, class D>
class memory_out_if
: virtual public sc_interface, virtual public portBase
{
public:
    // blocking req
    virtual void request(bool isWrite, const A&, D& ) = 0;
    virtual void requestNonBlocking(bool isWrite, const A&, D& data ) = 0; // non-blocking req for tee use only
    virtual void waitComplete(D&) = 0; // completion only on read

protected:
    // constructor
    memory_out_if() {}

private:
    // disabled
    memory_out_if( const memory_out_if<A, D>& );
    memory_out_if<A, D>& operator = ( const memory_out_if<A, D>& );
};

// ----------------------------------------------------------------------------
//  CLASS : memory_channel<T>
//
//  The memory_channel<T> primitive channel class.
// ----------------------------------------------------------------------------

template <class A, class D>
class memory_channel
: public memory_in_if<A, D>,
  public memory_out_if<A, D>,
  public sc_prim_channel
{
public:
    // constructor const char * module, std::string block
    explicit memory_channel( const char* name_, std::string block_, INTERFACE_AUTO_MODE autoModeReq=INTERFACE_AUTO_OFF, INTERFACE_AUTO_MODE autoModeData=INTERFACE_AUTO_OFF)
      : sc_prim_channel( name_ ),
        req_interfaceBase((std::string(name_) + "_req").c_str(), block_, autoModeReq),
        data_interfaceBase((std::string(name_) + "_data").c_str(), block_, autoModeData),
        m_channel_req_event( (std::string(name_) + "m_channel_req_event").c_str() ),
        m_channel_comp_event( (std::string(name_) + "m_channel_comp_event").c_str() ),
        m_reader(nullptr),
        m_writer(nullptr),
        m_valid(false),
        m_value_written(false)
        {
            req_interfaceBase.setTracker(A::getValueType());
            data_interfaceBase.setTracker(D::getValueType());
            logging::GetInstance().registerInterfaceStatus(std::string(name_), [this](void){ status();});
        }

    // destructor
    virtual ~memory_channel() { }

    // interface methods
    virtual void register_port( sc_port_base&, const char* ) override;

    // requester interface
    virtual void request(bool isWrite, const A&, D& ) override;
    virtual void requestNonBlocking(bool isWrite, const A&, D& data ) override; // non-blocking req for tee use only
    virtual void waitComplete(D&) override; // completion only on read
    // completer interface
    virtual void reqReceive(bool &isWrite, A&, D& ) override;
    virtual void complete(const D&) override ;

    void trace( sc_trace_file* tf ) const override;

    virtual void print( ::std::ostream& = ::std::cout ) const override;
    virtual void dump( ::std::ostream& = ::std::cout ) const override;
    virtual void status(void);

    virtual const char* kind() const override
        { return "memory_channel"; }

    // portBase overrides
    void setMultiDriver(std::string name, std::function<std::string(const uint64_t &value)> prt = nullptr) override
    {
        req_interfaceBase.setMultiDriver(name, prt);
        data_interfaceBase.setMultiDriver(name, prt);
    }
    std::shared_ptr<trackerBase> getTracker(void) override { return (data_interfaceBase.tracker_);} // just return the data tracker
    virtual void setTeeBusy(bool busy) override { req_interfaceBase.teeBusy_ = busy; data_interfaceBase.teeBusy_ = busy;}
    virtual void setTandem(void) override { req_interfaceBase.setTandem(); data_interfaceBase.setTandem(); }
    virtual void setLogging(verbosity_e verbosity) override { req_interfaceBase.setLogging(verbosity); data_interfaceBase.setLogging(verbosity); }
    virtual void setTimed(int nsec, timedDelayMode mode) override { req_interfaceBase.setTimed(nsec, mode); data_interfaceBase.setTimed(nsec, mode); }

protected:
    A   m_address; // typically this is the address field plus any user defined fields
    D   m_data;     // read or write data
    // for apb we can have trackers on both sides so instead of inheritance we use composition
    interfaceBase req_interfaceBase; // for req
    interfaceBase data_interfaceBase; // for data

    sc_event m_channel_req_event;
    sc_event m_channel_comp_event;

    sc_port_base* m_reader; // used for static design rule checking
    sc_port_base* m_writer; // used for static design rule checking

    bool m_in_progress = false;   // is a request in progress (PSEL)
    bool m_valid = false;         // can we read the value
    bool m_ready = false;
    bool m_data_available = false; // is read data available
    bool m_value_written = false; // does m_value contain data not this is seperated from the ready/valid for optimization of the task switches
    bool m_multi_writer = false;  //detect multiple writers
    bool m_isWrite = false;       // (PWRITE)

private:
    // disabled
    memory_channel( const memory_channel<A, D>& );
    memory_channel& operator = ( const memory_channel<A, D>& );
};

template <class A, class D>
inline void memory_channel<A, D>::register_port( sc_port_base& port_,
                const char* if_typename_ )
{
    std::string nm( if_typename_ );
    if( nm == typeid( memory_in_if<A, D> ).name() )
    {
        // only one reader can be connected
        if( m_reader != 0 ) {
            SC_REPORT_ERROR( SC_ID_MORE_THAN_ONE_FIFO_READER_, 0 );
            // may continue, if suppressed
        }
        m_reader = &port_;
    } else if( nm == typeid( memory_out_if<A, D> ).name() )
    {
        // only one writer can be connected
        if( m_writer != 0 ) {
            SC_REPORT_ERROR( SC_ID_MORE_THAN_ONE_FIFO_WRITER_, 0 );
            // may continue, if suppressed
        }
        m_writer = &port_;
    }
    else
    {
        SC_REPORT_ERROR( SC_ID_BIND_IF_TO_PORT_,
                         "memory_channel<A, D> port not recognized" );
        // may continue, if suppressed
    }
}

// blocking request
template <class A, class D>
inline void memory_channel<A, D>::reqReceive(bool &isWrite, A &addr, D &data)
{
    m_ready = true;
    if (!m_in_progress)
    {
        sc_core::wait(m_channel_req_event);
    }
    isWrite = m_isWrite;
    if (m_isWrite)
    {
        // we have a write so capture the data
        data = m_data;
        addr = m_address;
        uint64_t tag = addr.getStructValue();
        if (req_interfaceBase.log_.isMatch(LOG_NORMAL)) {
            req_interfaceBase.interfaceLog(std::string("write ")+addr.prt(req_interfaceBase.isDebugLog), tag);
        }
        tag = data.getStructValue();
        if (data_interfaceBase.log_.isMatch(LOG_NORMAL)) {
            data_interfaceBase.interfaceLog(std::string("write ")+data.prt(data_interfaceBase.isDebugLog), tag);
        }
        req_interfaceBase.delay();
        m_channel_comp_event.notify(SC_ZERO_TIME);
        m_value_written = false;
        m_in_progress = false;
    } else {
        addr = m_address;
        uint64_t tag = addr.getStructValue();
        if (req_interfaceBase.log_.isMatch(LOG_NORMAL)) {
            req_interfaceBase.interfaceLog(std::string("read ")+addr.prt(req_interfaceBase.isDebugLog), tag);
        }
    }
    m_ready = false;
}

// blocking read completion
template <class A, class D>
inline void memory_channel<A, D>::complete(const D& data )
{
    Q_ASSERT(m_isWrite==false && m_in_progress==true, "complete only valid on read");
    data_interfaceBase.delay();
    m_data = data;
    m_data_available = true;
    uint64_t tag = m_data.getStructValue();
    if (data_interfaceBase.log_.isMatch(LOG_NORMAL)) {
        std::ostringstream oss;
        oss << "read addr:" << m_address.prt(req_interfaceBase.isDebugLog) << " data:" << m_data.prt(data_interfaceBase.isDebugLog);
        data_interfaceBase.interfaceLog(oss.str(), tag);
    }
    m_in_progress = false;
    m_channel_comp_event.notify(SC_ZERO_TIME);
}

// blocking request

template <class A, class D>
inline void memory_channel<A, D>::request(bool isWrite, const A& address, D& data )
{
    // if we are reentering the write before the reader has had time to read the previous entry we need to block on the read event
    Q_ASSERT(m_multi_writer==false, "multiple threads driving interface");
    m_multi_writer = true;
    // for the write case we may need to wait for the previous operation to complete
    if (m_in_progress)
    {
        Q_ASSERT(m_isWrite==true, "read in progress!");
        sc_core::wait(m_channel_comp_event);
    }
    req_interfaceBase.delay();
    if (isWrite)
    {
        // wait for previous write to complete
        m_in_progress = true;
        m_isWrite = isWrite;
        m_value_written = true;
        m_data = data;
        m_valid = true;
        m_address = address;
        if (m_ready)
        {
            m_channel_req_event.notify(SC_ZERO_TIME);
        }
    } else {
        m_in_progress = true;
        m_data_available = false;
        m_isWrite = isWrite;
        m_address = address;
        if (m_ready)
        {
            m_channel_req_event.notify(SC_ZERO_TIME);
        }
        sc_core::wait(m_channel_comp_event);
        data = m_data;
        m_in_progress = false;
    }
    m_multi_writer = false;
}

template <class A, class D>
inline void memory_channel<A, D>::requestNonBlocking(bool isWrite, const A& address, D& data )
{
    // if we are reentering the write before the reader has had time to read the previous entry we need to block on the read event
    Q_ASSERT(m_multi_writer==false, "multiple threads driving interface");
    m_multi_writer = true;
    // for the write case we may need to wait for the previous operation to complete
    if (m_in_progress)
    {
        Q_ASSERT(m_isWrite==true, "read in progress!");
        sc_core::wait(m_channel_comp_event);
    }
    req_interfaceBase.delay();
    if (isWrite)
    {
        // wait for previous write to complete
        m_in_progress = true;
        m_isWrite = isWrite;
        m_value_written = true;
        m_data = data;
        m_valid = true;
        m_address = address;
        if (m_ready)
        {
            m_channel_req_event.notify(SC_ZERO_TIME);
        }
    } else {
        m_in_progress = true;
        m_data_available = false;
        m_isWrite = isWrite;
        m_address = address;
        if (m_ready)
        {
            m_channel_req_event.notify(SC_ZERO_TIME);
        }
    }
}

template <class A, class D>
inline void memory_channel<A, D>::waitComplete(D& data )
{
    // if we are reentering the write before the reader has had time to read the previous entry we need to block on the read event

    if (m_isWrite) {
        // for the write case we may need to wait for the previous operation to complete
        if (m_in_progress)
        {
            sc_core::wait(m_channel_comp_event);
        }
    } else {
        if (!m_data_available)
        {
            sc_core::wait(m_channel_comp_event);
        }
        data = m_data;
    }
    m_in_progress = false;
    m_multi_writer = false;
}


template <class A, class D>
void memory_channel<A, D>::status(void)
{
    if (m_in_progress)
    {
        req_interfaceBase.log_.logPrint(
            fmt::format("{} has data/or no ack received m_valid:{} m_ready:{} m_data_available:{} m_value_written:{} m_isWrite:{} ",
              name(), (uint16_t)m_valid, (uint16_t)m_ready, (uint16_t)m_data_available, (uint16_t)m_value_written, (uint16_t)m_isWrite), LOG_IMPORTANT );
        dump();
    }
    req_interfaceBase.teeStatus();
}

template <class A, class D>
inline void memory_channel<A, D>::trace( sc_trace_file* tf ) const
{
    (void) tf; /* ignore potentially unused parameter */
}


template <class A, class D>
inline void memory_channel<A, D>::print( ::std::ostream& os ) const
{
    os << m_address.prt(req_interfaceBase.isDebugLog) << '\n';
}

template <class A, class D>
inline void memory_channel<A, D>::dump( ::std::ostream& os ) const
{
    if (m_value_written)
    {
        os << m_address.prt(req_interfaceBase.isDebugLog) << '\n';
    } else {
        os << "no value" << '\n';
    }
}

template <class A, class D>
inline ::std::ostream& operator << ( ::std::ostream& os, const memory_channel<A, D>& a )
{
    a.print( os );
    return os;
}

} // namespace sc_core

template <class A, class D>
using memory_out = sc_port<memory_out_if<A, D> >;
template <class A, class D>
using memory_in = sc_port<memory_in_if<A, D> >;

#endif // MEMORY_CHANNEL_H
