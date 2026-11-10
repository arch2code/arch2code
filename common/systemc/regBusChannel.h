// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef REGBUSCHANNEL_H
#define REGBUSCHANNEL_H

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


// ----------------------------------------------------------------------------
//  CLASS : regBusChannel<R, D, IN_IF, OUT_IF>
//
//  One register-bus transfer at a time between a requester (OUT_IF) and a
//  completer (IN_IF). A protocol channel derives from it with its own
//  interface classes, so its ports bind only to channels of that protocol.
// ----------------------------------------------------------------------------

template <class R, class D, class IN_IF, class OUT_IF>
class regBusChannel
: public IN_IF,
  public OUT_IF,
  public sc_prim_channel
{
public:
    // constructor const char * module, std::string block
    regBusChannel( const char* name_, std::string block_, INTERFACE_AUTO_MODE autoModeReq, INTERFACE_AUTO_MODE autoModeData)
      : sc_prim_channel( name_ ),
        req_interfaceBase((std::string(name_) + "_req").c_str(), block_, autoModeReq, TIMED_DELAY_APPLIES),
        data_interfaceBase((std::string(name_) + "_data").c_str(), block_, autoModeData, TIMED_DELAY_APPLIES),
        m_channel_req_event( (std::string(name_) + "m_channel_req_event").c_str() ),
        m_channel_comp_event( (std::string(name_) + "m_channel_comp_event").c_str() ),
        m_reader(nullptr),
        m_writer(nullptr),
        m_value_written(false)
        {
            req_interfaceBase.setTracker(R::getValueType());
            data_interfaceBase.setTracker(D::getValueType());
            logging::GetInstance().registerInterfaceStatus(std::string(name_), [this](void){ status();});
        }

    // destructor
    virtual ~regBusChannel() { }

    // interface methods
    virtual void register_port( sc_port_base&, const char* ) override;

    // requester interface
    virtual void request(bool isWrite, const R&, D& ) override;
    virtual bool requestWithResponse(bool isWrite, const R&, D& ) override;
    virtual void requestNonBlocking(bool isWrite, const R&, D& data ) override; // non-blocking req for tee use only
    virtual void waitComplete(D&) override; // completion only on read
    virtual void requestNonBlockingWithResponse(bool isWrite, const R&, D& data ) override;
    virtual bool waitCompleteWithResponse(D&) override;
    // completer interface
    virtual void reqReceive(bool &isWrite, R&, D& ) override;
    virtual void complete(const D&, bool slverr = false) override;
    virtual bool receivedWantsResponse() override { return m_received_wants_response; }
    virtual bool isActive() override { return(m_req_pending); }
    virtual bool isNotActive() override { return(!m_req_pending); }
    virtual void setExternalEvent( sc_event *event ) override
    {
        m_external_event_ptr = event;
        m_external_arb = true;
    }

    void trace( sc_trace_file* tf ) const override;

    virtual void print( ::std::ostream& = ::std::cout ) const override;
    virtual void dump( ::std::ostream& = ::std::cout ) const override;
    virtual void status(void);

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
    virtual sc_prim_channel* getChannel(void) override { return this; }

protected:
    R   m_req_data; // typically this is the address field plus any user defined fields
    D   m_data;     // read or write data
    // a register bus can have trackers on both sides so instead of inheritance we use composition
    interfaceBase req_interfaceBase; // for req
    interfaceBase data_interfaceBase; // for data

    sc_event m_channel_req_event;
    sc_event m_channel_comp_event;

    sc_port_base* m_reader; // used for static design rule checking
    sc_port_base* m_writer; // used for static design rule checking

    // Protocol state:
    // - m_req_pending: one outstanding request at a time.
    // - m_req_is_write: the outstanding request is a write.
    // - m_resp_pending: a completed response, including its error bit.
    //
    // Events are wakeups only; state lives in these flags and must be checked in
    // guarded wait loops to avoid missed notifications.
    bool m_req_pending = false;
    bool m_req_is_write = false;
    bool m_req_wait_response = false;
    bool m_resp_pending = false;
    bool m_slverr = false;
    // The last received request was a posted write, already acknowledged by
    // reqReceive(). A complete() for it must not touch the requester's next
    // request, which may already be pending.
    bool m_received_posted_write = false;
    bool m_received_wants_response = false;
    bool m_value_written = false; // does m_value contain data not this is seperated from the ready/valid for optimization of the task switches
    bool m_multi_writer = false;  //detect multiple writers
    bool m_external_arb = false;
    sc_event* m_external_event_ptr = nullptr;

private:
    // disabled
    regBusChannel( const regBusChannel& );
    regBusChannel& operator = ( const regBusChannel& );
};

template <class R, class D, class IN_IF, class OUT_IF>
inline void regBusChannel<R, D, IN_IF, OUT_IF>::register_port( sc_port_base& port_,
                const char* if_typename_ )
{
    std::string nm( if_typename_ );
    if( nm == typeid( IN_IF ).name() )
    {
        // only one reader can be connected
        if( m_reader != 0 ) {
            SC_REPORT_ERROR( SC_ID_MORE_THAN_ONE_FIFO_READER_, 0 );
            // may continue, if suppressed
        }
        m_reader = &port_;
    } else if( nm == typeid( OUT_IF ).name() )
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
                         "register bus channel port not recognized" );
        // may continue, if suppressed
    }
}

// blocking request
template <class R, class D, class IN_IF, class OUT_IF>
inline void regBusChannel<R, D, IN_IF, OUT_IF>::reqReceive(bool &isWrite, R &req, D &data)
{
    while (!m_req_pending)
    {
        sc_core::wait(m_channel_req_event);
    }

    isWrite = m_req_is_write;

    if (m_req_is_write)
    {
        // Legacy writes acknowledge here; response-aware writes wait for complete().
        data = m_data;
        req = m_req_data;
        uint64_t tag = req.getStructValue();
        if (req_interfaceBase.log_.isMatch(LOG_NORMAL)) {
            req_interfaceBase.interfaceLog(std::string("write " ) + req.prt(req_interfaceBase.isDebugLog), tag);
        }
        tag = data.getStructValue();
        if (data_interfaceBase.log_.isMatch(LOG_NORMAL)) {
            data_interfaceBase.interfaceLog(std::string("write " ) + data.prt(data_interfaceBase.isDebugLog), tag);
        }
        req_interfaceBase.delay();

        m_value_written = false;
        m_received_wants_response = m_req_wait_response;
        m_received_posted_write = !m_req_wait_response;
        if (!m_req_wait_response) {
            m_req_pending = false;
            m_channel_comp_event.notify(SC_ZERO_TIME);
        }
        return;
    }

    // read: capture request fields; response arrives via complete()
    m_received_wants_response = m_req_wait_response;
    m_received_posted_write = false;
    req = m_req_data;
    uint64_t tag = req.getStructValue();
    if (req_interfaceBase.log_.isMatch(LOG_NORMAL)) {
        req_interfaceBase.interfaceLog(std::string("read " ) + req.prt(req_interfaceBase.isDebugLog), tag);
    }
}


// Blocking response completion.
template <class R, class D, class IN_IF, class OUT_IF>
inline void regBusChannel<R, D, IN_IF, OUT_IF>::complete(const D& data, bool slverr)
{
    if (m_received_posted_write) {
        m_received_posted_write = false;
        return;
    }
    Q_ASSERT(m_req_pending, "complete without an outstanding request");

    if (!m_req_is_write) {
        data_interfaceBase.delay();
        m_data = data;
    }
    m_slverr = slverr;
    m_resp_pending = true;

    uint64_t tag = m_req_is_write ? m_req_data.getStructValue() : m_data.getStructValue();
    if (!m_req_is_write && data_interfaceBase.log_.isMatch(LOG_NORMAL)) {
        std::ostringstream oss;
        oss << "read req:" << m_req_data.prt(req_interfaceBase.isDebugLog)
            << " data:" << m_data.prt(data_interfaceBase.isDebugLog);
        data_interfaceBase.interfaceLog(oss.str(), tag);
    }

    m_req_pending = false;
    m_channel_comp_event.notify(SC_ZERO_TIME);
}


// Blocking request.
template <class R, class D, class IN_IF, class OUT_IF>
inline void regBusChannel<R, D, IN_IF, OUT_IF>::request(bool isWrite, const R& request, D& data )
{
    Q_ASSERT(m_multi_writer==false, "multiple threads driving interface");
    m_multi_writer = true;

    // Single outstanding transaction per channel.
    if (m_req_pending)
    {
        Q_ASSERT(m_req_is_write==true, "read in progress!");
        while (m_req_pending)
        {
            sc_core::wait(m_channel_comp_event);
        }
    }

    req_interfaceBase.delay();

    if (isWrite)
    {
        m_req_pending = true;
        m_req_is_write = true;
        m_value_written = true;
        m_data = data;
        m_req_data = request;
        m_channel_req_event.notify(SC_ZERO_TIME);
        if (m_external_arb) {
            m_external_event_ptr->notify(SC_ZERO_TIME);
        }
        m_multi_writer = false;
        return;
    }

    // read
    m_req_pending = true;
    m_req_is_write = false;
    m_resp_pending = false;
    m_req_data = request;
    m_channel_req_event.notify(SC_ZERO_TIME);
    if (m_external_arb) {
        m_external_event_ptr->notify(SC_ZERO_TIME);
    }

    while (!m_resp_pending)
    {
        sc_core::wait(m_channel_comp_event);
    }

    data = m_data;
    m_resp_pending = false;
    m_multi_writer = false;
}

// Blocking request that returns the response error bit for both reads and writes.
template <class R, class D, class IN_IF, class OUT_IF>
inline bool regBusChannel<R, D, IN_IF, OUT_IF>::requestWithResponse(bool isWrite, const R& request, D& data)
{
    Q_ASSERT(m_multi_writer==false, "multiple threads driving interface");
    m_multi_writer = true;

    if (m_req_pending)
    {
        Q_ASSERT(m_req_is_write==true, "read in progress!");
        while (m_req_pending)
        {
            sc_core::wait(m_channel_comp_event);
        }
    }

    req_interfaceBase.delay();

    m_req_pending = true;
    m_req_is_write = isWrite;
    m_req_wait_response = true;
    m_resp_pending = false;
    m_slverr = false;
    m_req_data = request;
    if (isWrite) {
        m_value_written = true;
        m_data = data;
    }
    m_channel_req_event.notify(SC_ZERO_TIME);
    if (m_external_arb) {
        m_external_event_ptr->notify(SC_ZERO_TIME);
    }

    while (!m_resp_pending)
    {
        sc_core::wait(m_channel_comp_event);
    }

    if (!isWrite) {
        data = m_data;
    }
    const bool slverr = m_slverr;
    m_resp_pending = false;
    m_req_wait_response = false;
    m_multi_writer = false;
    return slverr;
}


template <class R, class D, class IN_IF, class OUT_IF>
inline void regBusChannel<R, D, IN_IF, OUT_IF>::requestNonBlocking(bool isWrite, const R& request, D& data )
{
    Q_ASSERT(m_multi_writer==false, "multiple threads driving interface");
    m_multi_writer = true;

    if (m_req_pending)
    {
        Q_ASSERT(m_req_is_write==true, "read in progress!");
        while (m_req_pending)
        {
            sc_core::wait(m_channel_comp_event);
        }
    }

    req_interfaceBase.delay();

    if (isWrite)
    {
        m_req_pending = true;
        m_req_is_write = true;
        m_value_written = true;
        m_data = data;
        m_req_data = request;
        m_channel_req_event.notify(SC_ZERO_TIME);
        if (m_external_arb) {
            m_external_event_ptr->notify(SC_ZERO_TIME);
        }
        return;
    }

    // read
    m_req_pending = true;
    m_req_is_write = false;
    m_resp_pending = false;
    m_req_data = request;
    m_channel_req_event.notify(SC_ZERO_TIME);
    if (m_external_arb) {
        m_external_event_ptr->notify(SC_ZERO_TIME);
    }
}


template <class R, class D, class IN_IF, class OUT_IF>
inline void regBusChannel<R, D, IN_IF, OUT_IF>::waitComplete(D& data )
{
    if (m_req_is_write)
    {
        while (m_req_pending)
        {
            sc_core::wait(m_channel_comp_event);
        }
        m_multi_writer = false;
        return;
    }

    while (!m_resp_pending)
    {
        sc_core::wait(m_channel_comp_event);
    }

    data = m_data;
    // Leave m_resp_pending asserted so a subsequent waitComplete() (used by some adapters)
    // can return immediately without deadlocking.
    m_multi_writer = false;
}

template <class R, class D, class IN_IF, class OUT_IF>
inline void regBusChannel<R, D, IN_IF, OUT_IF>::requestNonBlockingWithResponse(bool isWrite, const R& request, D& data )
{
    Q_ASSERT(m_multi_writer==false, "multiple threads driving interface");
    m_multi_writer = true;

    if (m_req_pending)
    {
        Q_ASSERT(m_req_is_write==true, "read in progress!");
        while (m_req_pending)
        {
            sc_core::wait(m_channel_comp_event);
        }
    }

    req_interfaceBase.delay();

    m_req_pending = true;
    m_req_is_write = isWrite;
    m_req_wait_response = true;
    m_resp_pending = false;
    m_slverr = false;
    m_req_data = request;
    if (isWrite) {
        m_value_written = true;
        m_data = data;
    }
    m_channel_req_event.notify(SC_ZERO_TIME);
    if (m_external_arb) {
        m_external_event_ptr->notify(SC_ZERO_TIME);
    }
}

template <class R, class D, class IN_IF, class OUT_IF>
inline bool regBusChannel<R, D, IN_IF, OUT_IF>::waitCompleteWithResponse(D& data )
{
    while (!m_resp_pending)
    {
        sc_core::wait(m_channel_comp_event);
    }
    if (!m_req_is_write) {
        data = m_data;
    }
    const bool slverr = m_slverr;
    m_resp_pending = false;
    m_req_wait_response = false;
    m_multi_writer = false;
    return slverr;
}




template <class R, class D, class IN_IF, class OUT_IF>
void regBusChannel<R, D, IN_IF, OUT_IF>::status(void)
{
    if (m_req_pending || m_resp_pending)
    {
        req_interfaceBase.log_.logPrint(
            std::format(
                "{} has data/or no ack received req_pending:{} resp_pending:{} value_written:{} req_is_write:{} ",
                name(),
                (uint16_t)m_req_pending,
                (uint16_t)m_resp_pending,
                (uint16_t)m_value_written,
                (uint16_t)m_req_is_write),
            LOG_IMPORTANT);
        dump();
    }
    req_interfaceBase.teeStatus();
}


template <class R, class D, class IN_IF, class OUT_IF>
inline void regBusChannel<R, D, IN_IF, OUT_IF>::trace( sc_trace_file* tf ) const
{
    (void) tf; /* ignore potentially unused parameter */
}


template <class R, class D, class IN_IF, class OUT_IF>
inline void regBusChannel<R, D, IN_IF, OUT_IF>::print( ::std::ostream& os ) const
{
    os << m_req_data.prt(req_interfaceBase.isDebugLog) << '\n';
}

template <class R, class D, class IN_IF, class OUT_IF>
inline void regBusChannel<R, D, IN_IF, OUT_IF>::dump( ::std::ostream& os ) const
{
    if (m_value_written)
    {
        os << m_req_data.prt(req_interfaceBase.isDebugLog) << '\n';
    } else {
        os << "no value" << '\n';
    }
}

template <class R, class D, class IN_IF, class OUT_IF>
inline ::std::ostream& operator << ( ::std::ostream& os, const regBusChannel<R, D, IN_IF, OUT_IF>& a )
{
    a.print( os );
    return os;
}

#endif // REGBUSCHANNEL_H
