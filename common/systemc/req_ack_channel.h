// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef REQ_ACK_CHANNEL_H
#define REQ_ACK_CHANNEL_H

#include "sysc/communication/sc_communication_ids.h"
#include "sysc/communication/sc_prim_channel.h"
#include "sysc/kernel/sc_event.h"
#include "sysc/kernel/sc_simcontext.h"
#include "sysc/tracing/sc_trace.h"
#include <typeinfo>
#include <iostream>
#include "portBase.h"
#include "interfaceBase.h"
#include "synchLock.h"

namespace sc_core {

// req(R, &A)
// |        ---R----> reqReceive(R)
// |                     |
// |<----------A---- ack(A)

template <class R, class A>
class req_ack_in_if
: virtual public sc_interface,  virtual public portBase
{
public:

    // blocking read
    virtual void reqReceive( R& ) = 0;
    virtual void ack(const A&) = 0;
    virtual bool isActive() = 0;
    virtual bool isNotActive() = 0;
    virtual void setExternalEvent( sc_event *event ) = 0;

protected:
    // constructor
    req_ack_in_if()
        {}

private:
    // disabled
    req_ack_in_if( const req_ack_in_if<R, A>& );
    req_ack_in_if<R, A>& operator = ( const req_ack_in_if<R, A>& );
};

template <class R, class A>
class req_ack_out_if
: virtual public sc_interface, virtual public portBase
{
public:
    // blocking req
    virtual void req( const R&, A&, uint64_t userMagic = (uint64_t)-1 ) = 0;
    // non-blocking variant for tee use case
    virtual void reqNonBlocking( const R& req_, uint64_t userMagic = (uint64_t)-1) = 0;
    virtual void waitAck( A& ack_  ) = 0;

protected:
    // constructor
    req_ack_out_if()
        {}

private:
    // disabled
    req_ack_out_if( const req_ack_out_if<R, A>& );
    req_ack_out_if<R, A>& operator = ( const req_ack_out_if<R, A>& );
};

// ----------------------------------------------------------------------------
//  CLASS : req_ack_channel<T>
//
//  The req_ack_channel<T> primitive channel class.
// ----------------------------------------------------------------------------

template <class R, class A>
class req_ack_channel
: public req_ack_in_if<R, A>,
  public req_ack_out_if<R, A>,
  public sc_prim_channel
{
public:
    // constructor const char * module, std::string block
    explicit req_ack_channel( const char* name_, std::string block_, INTERFACE_AUTO_MODE autoModeReq=INTERFACE_AUTO_OFF, INTERFACE_AUTO_MODE autoModeAck=INTERFACE_AUTO_OFF)
      : sc_prim_channel( name_ ),
        req_interfaceBase((std::string(name_) + "_req").c_str(), block_, autoModeReq),
        ack_interfaceBase((std::string(name_) + "_ack").c_str(), block_, autoModeAck),
        m_channel_req_event( (std::string(name_) + "m_channel_req_event").c_str() ),
        m_channel_req_event_ptr(&m_channel_req_event),
        m_channel_ack_event( (std::string(name_) + "m_channel_ack_event").c_str() ),
        m_reader(nullptr),
        m_writer(nullptr),
        m_active(false),
        m_waiting(false),
        m_done(false),
        m_value_written(false)
        {
            req_interfaceBase.setTracker(R::getValueType());
            ack_interfaceBase.setTracker(A::getValueType());
            logging::GetInstance().registerInterfaceStatus(std::string(name_), [this](void){ status();});
        }

    // destructor
    virtual ~req_ack_channel() { }

    // interface methods
    virtual void register_port( sc_port_base&, const char* ) override;

    // initiator interface
    virtual void req( const R&, A&, uint64_t userMagic ) override;
    // target interface
    virtual void reqReceive( R& ) override;
    virtual void ack(const A&) override;
    virtual bool isActive() override { return(m_active); }
    virtual bool isNotActive() override { return(!m_active); }

    // non-blocking variant for tee use case
    virtual void reqNonBlocking( const R& req_, uint64_t userMagic) override;
    virtual void waitAck( A& ack_  ) override;

    void trace( sc_trace_file* tf ) const override;

    virtual void print( ::std::ostream& = ::std::cout ) const override;
    virtual void dump( ::std::ostream& = ::std::cout ) const override;
    virtual void status(void);

    virtual const char* kind() const override
        { return "req_ack_channel"; }
    virtual void setExternalEvent( sc_event *event ) override
    {
        m_channel_req_event_ptr = event;
        m_external_arb = true;
    }

    // portBase overrides
    void setMultiDriver(std::string name, std::function<std::string(const uint64_t &value)> prt = nullptr) override
    {
        req_interfaceBase.setMultiDriver(name, prt);
    }
    std::shared_ptr<trackerBase> getTracker(void) override { return (req_interfaceBase.tracker_);} // just return the req tracker
    virtual void setTeeBusy(bool busy) override { req_interfaceBase.teeBusy_ = busy; }
    virtual void setTandem(void) override { req_interfaceBase.setTandem(); ack_interfaceBase.setTandem(); }
    virtual void setLogging(verbosity_e verbosity) override { req_interfaceBase.setLogging(verbosity); ack_interfaceBase.setLogging(verbosity); }
    virtual void setTimed(int nsec, timedDelayMode mode) override { req_interfaceBase.setTimed(nsec, mode); ack_interfaceBase.setTimed(nsec, mode); }

protected:
    R   m_req_data;
    A   m_ack_data;
    // for reqAck we can have trackers on both sides so instead of inheritance we use composition
    interfaceBase req_interfaceBase; // for req
    interfaceBase ack_interfaceBase; // for ack

    sc_event m_channel_req_event;
    sc_event* m_channel_req_event_ptr;
    sc_event m_channel_ack_event;

    sc_port_base* m_reader; // used for static design rule checking
    sc_port_base* m_writer; // used for static design rule checking

    bool m_active = false;   // req issued / waiting for ack
    bool m_waiting = false; // waiting for req
    bool m_done = false; // ack done
    bool m_value_written = false; // m_value contain valid data when true
    bool m_multi_writer = false; //detect multiple writers
    bool m_external_arb = false;

private:
    // disabled
    req_ack_channel( const req_ack_channel<R, A>& );
    req_ack_channel& operator = ( const req_ack_channel<R, A>& );
};

template <class R, class A>
inline void req_ack_channel<R, A>::register_port( sc_port_base& port_,
                const char* if_typename_ )
{
    std::string nm( if_typename_ );
    if( nm == typeid( req_ack_in_if<R, A> ).name() )
    {
        // only one reader can be connected
        if( m_reader != 0 ) {
            SC_REPORT_ERROR( SC_ID_MORE_THAN_ONE_FIFO_READER_, 0 );
            // may continue, if suppressed
        }
        m_reader = &port_;
    } else if( nm == typeid( req_ack_out_if<R, A> ).name() )
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
                         "req_ack_channel<T> port not recognized" );
        // may continue, if suppressed
    }
}

// blocking request
template <class R, class A>
inline void req_ack_channel<R, A>::reqReceive( R& req_ )
{
    m_waiting = true;
    if (!m_active)
    {
        sc_core::wait(*m_channel_req_event_ptr);
    }
    req_ = m_req_data;
    m_value_written = false;
    m_waiting = false;
    uint64_t tag = req_.getStructValue();
    if (req_interfaceBase.log_.isMatch(LOG_NORMAL)) {
        req_interfaceBase.interfaceLog(req_.prt(req_interfaceBase.isDebugLog), tag);
    }
}

// blocking read
template <class R, class A>
inline void req_ack_channel<R, A>::ack(const A& ack_ )
{
    ack_interfaceBase.delay(false);
    m_active = false;
    m_ack_data = ack_;
    m_done = true;
    m_channel_ack_event.notify(SC_ZERO_TIME);
}

// blocking write

template <class R, class A>
inline void req_ack_channel<R, A>::req( const R& req_, A& ack_, uint64_t userMagic  )
{
    // if we are reentering the write before the reader has had time to read the previous entry we need to block on the read event
    if (req_interfaceBase.isLocking())
    {
        uint64_t magicValue = userMagic;
        if (magicValue == (uint64_t)-1)
        {
            magicValue = req_.getStructValue();
            if (magicValue == (uint64_t)-1) {
                typename R::_packedSt packed;
                req_.pack(packed);
                magicValue = fnv1a_hash((uint8_t *)&packed, R::_byteWidth);
            }
        }
        req_interfaceBase.synchLock_->lock(magicValue);
    }
    Q_ASSERT(m_multi_writer==false, "multiple threads driving interface");
    m_multi_writer = true;
    req_interfaceBase.delay(false);
    m_value_written = true;
    m_req_data = req_;
    m_active = true;
    // for external arb case, we will not be in the read function so we need to unconditionally notify the event
    if (m_waiting || m_external_arb)
    {
        m_channel_req_event_ptr->notify(SC_ZERO_TIME);
    }
    sc_core::wait(m_channel_ack_event);
    ack_ = m_ack_data;
    uint64_t tag = ack_.getStructValue();
    if (ack_interfaceBase.log_.isMatch(LOG_NORMAL)) {
        ack_interfaceBase.interfaceLog(ack_.prt(ack_interfaceBase.isDebugLog), tag);
    }
    m_multi_writer = false;
    if (req_interfaceBase.isLocking())
    {
        req_interfaceBase.synchLock_->unlock();
    }
}

// non-blocking req must be paired with non-blocking waitAck - this is ONLY for Tee usecase
template <class R, class A>
inline void req_ack_channel<R, A>::reqNonBlocking( const R& req_, uint64_t userMagic)
{
    if (req_interfaceBase.isLocking())
    {
        uint64_t magicValue = userMagic;
        if (magicValue == (uint64_t)-1)
        {
            magicValue = req_.getStructValue();
            if (magicValue == (uint64_t)-1) {
                typename R::_packedSt packed;
                req_.pack(packed);
                magicValue = fnv1a_hash((uint8_t *)&packed, R::_byteWidth);
            }
        }
        req_interfaceBase.synchLock_->lock(magicValue);
    }
    // if we are reentering the write before the reader has had time to read the previous entry we need to block on the read event
    Q_ASSERT(m_multi_writer==false, "multiple threads driving interface");
    m_multi_writer = true;
    req_interfaceBase.delay(false);
    m_value_written = true;
    m_req_data = req_;
    m_active = true;
    m_done = false;
    // for external arb case, we will not be in the read function so we need to unconditionally notify the event
    if (m_waiting || m_external_arb)
    {
        m_channel_req_event_ptr->notify(SC_ZERO_TIME);
    }
}

// this is ONLY for Tee usecase
template <class R, class A>
inline void req_ack_channel<R, A>::waitAck( A& ack_  )
{
    if (!m_done)
    {
        sc_core::wait(m_channel_ack_event);
    }
    ack_ = m_ack_data;
    uint64_t tag = ack_.getStructValue();
    if (ack_interfaceBase.log_.isMatch(LOG_NORMAL)) {
        ack_interfaceBase.interfaceLog(ack_.prt(ack_interfaceBase.isDebugLog), tag);
    }
    m_multi_writer = false;
    if (req_interfaceBase.isLocking())
    {
        req_interfaceBase.synchLock_->unlock();
    }
}

template <class R, class A>
void req_ack_channel<R, A>::status(void)
{
    if (m_value_written == true)
    {
        req_interfaceBase.log_.logPrint(std::format("{} has data/or no ack received", name()  ), LOG_IMPORTANT );
        dump();
    }
    req_interfaceBase.teeStatus();
}

template <class R, class A>
inline void req_ack_channel<R, A>::trace( sc_trace_file* tf ) const
{
    (void) tf; /* ignore potentially unused parameter */
}


template <class R, class A>
inline void req_ack_channel<R, A>::print( ::std::ostream& os ) const
{
    os << m_req_data.prt(req_interfaceBase.isDebugLog) << '\n';
}

template <class R, class A>
inline void req_ack_channel<R, A>::dump( ::std::ostream& os ) const
{
    if (m_value_written)
    {
        os << m_req_data.prt(req_interfaceBase.isDebugLog) << '\n';
    } else {
        os << "no value" << '\n';
    }
}

template <class R, class A>
inline ::std::ostream& operator << ( ::std::ostream& os, const req_ack_channel< R, A>& a )
{
    a.print( os );
    return os;
}

} // namespace sc_core

template <class R, class A>
using req_ack_out = sc_port<req_ack_out_if< R, A > >;
template <class R, class A>
using req_ack_in = sc_port<req_ack_in_if<  R, A > >;

#endif // REQ_ACK_CHANNEL_H
