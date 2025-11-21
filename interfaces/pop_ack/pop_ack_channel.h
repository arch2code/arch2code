// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef POP_ACK_CHANNEL_H
#define POP_ACK_CHANNEL_H

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
#include <format>

// pop( &A )
// |        -------> popReceive( )
// |                     |
// |<----------A---- ack(A)

namespace sc_core {

template <class A>
class pop_ack_in_if
: virtual public sc_interface, virtual public portBase
{
public:

    // blocking read
    virtual void popReceive( ) = 0;
    virtual void ack(const A&) = 0;
    virtual bool isActive() = 0;
    virtual bool isNotActive() = 0;
    virtual void setExternalEvent( sc_event *event ) = 0;

protected:
    // constructor
    pop_ack_in_if() {}

private:
    // disabled
    pop_ack_in_if( const pop_ack_in_if<A>& );
    pop_ack_in_if<A>& operator = ( const pop_ack_in_if<A>& );
};


template <class A>
class pop_ack_out_if
: virtual public sc_interface, virtual public portBase
{
public:
    // blocking pop
    virtual void pop( A&, int magicValue=0 ) = 0;
    // non-blocking variant for tee use case
    virtual void popNonBlocking( void ) = 0;
    virtual void waitAck( A& ack_ ) = 0;

protected:
    // constructor
    pop_ack_out_if() {}

private:
    // disabled
    pop_ack_out_if( const pop_ack_out_if<A>& );
    pop_ack_out_if<A>& operator = ( const pop_ack_out_if<A>& );
};

template <class A>
class pop_ack_channel
: public pop_ack_in_if<A>,
  public pop_ack_out_if<A>,
  public sc_prim_channel,
  public interfaceBase
{
public:
    // constructor const char * module, std::string block
    explicit pop_ack_channel( const char* name_, std::string block_, INTERFACE_AUTO_MODE autoMode=INTERFACE_AUTO_OFF)
      : sc_prim_channel( name_ ),
        interfaceBase(name_, block_, autoMode),
        m_channel_pop_event( (std::string(name_) + "m_channel_pop_event").c_str() ),
        m_channel_pop_event_ptr( &m_channel_pop_event ),
        m_channel_ack_event( (std::string(name_) + "m_channel_ack_event").c_str() ),
        m_reader(nullptr),
        m_writer(nullptr),
        m_active(false),
        m_waiting(false),
        m_done(false),
        m_value_written(false)
        {
            setTracker(A::getValueType());
            logging::GetInstance().registerInterfaceStatus(std::string(name_), [this](void){ status();});
        }

    // destructor
    virtual ~pop_ack_channel() { }

    // interface methods
    virtual void register_port( sc_port_base&, const char* ) override;

    // initiator interface
    virtual void pop( A&, int magicValue = 0 ) override;
    // non-blocking variant for tee use case
    virtual void popNonBlocking( void ) override;
    virtual void waitAck( A& ack_ ) override;
    // target interface
    virtual void popReceive( ) override;
    virtual void ack(const A&) override;
    virtual bool isActive() override { return(m_active); }
    virtual bool isNotActive() override { return(!m_active); }
    virtual void setExternalEvent( sc_event *event ) override
    {
        m_channel_pop_event_ptr = event;
        m_external_arb = true;
    }

    void trace( sc_trace_file* tf ) const override;

    virtual void print( ::std::ostream& = ::std::cout ) const override;
    virtual void dump( ::std::ostream& = ::std::cout ) const override;
    virtual void status(void);

    virtual const char* kind() const override
        { return "pop_ack_channel"; }

    // portBase overrides
    void setMultiDriver(std::string name_, std::function<std::string(const uint64_t &value)> prt = nullptr) override
    {
        Q_ASSERT(false, std::format("multiple drivers on {} pop_ack interface is invalid", name_ ));
    }
    std::shared_ptr<trackerBase> getTracker(void) override { return (tracker_);}
    virtual void setTeeBusy(bool busy) override { teeBusy_ = busy; }
    virtual void setTandem(void) override { interfaceBase::setTandem(); }
    // virtual void setLogging(loglevel_e loglevel) override { interfaceBase::setLogging(loglevel); }
    virtual void setLogging(verbosity_e verbosity) override { interfaceBase::setLogging(verbosity); }
    virtual void setTimed(int nsec, timedDelayMode mode) override { interfaceBase::setTimed(nsec, mode); }

protected:
    A   m_ack_data;

    sc_event m_channel_pop_event;
    sc_event *m_channel_pop_event_ptr;
    sc_event m_channel_ack_event;

    sc_port_base* m_reader; // used for static design rule checking
    sc_port_base* m_writer; // used for static design rule checking

    bool m_active = false;   // pop issued / waiting for ack
    bool m_waiting = false; // waiting for pop
    bool m_done = false; // ack done
    bool m_value_written = false; // m_value contain valid data when true
    bool m_multi_writer = false; //detect multiple writers
    bool m_external_arb = false;

private:
    // disabled
    pop_ack_channel( const pop_ack_channel<A>& );
    pop_ack_channel& operator = ( const pop_ack_channel<A>& );
};

template <class A>
inline void pop_ack_channel<A>::register_port( sc_port_base& port_,
                const char* if_typename_ )
{
    std::string nm( if_typename_ );
    if( nm == typeid( pop_ack_in_if<A> ).name() )
    {
        // only one reader can be connected
        if( m_reader != 0 ) {
            SC_REPORT_ERROR( SC_ID_MORE_THAN_ONE_FIFO_READER_, 0 );
            // may continue, if suppressed
        }
        m_reader = &port_;
    } else if( nm == typeid( pop_ack_out_if<A> ).name() )
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
                         "pop_ack_channel<T> port not recognized" );
        // may continue, if suppressed
    }
}

// blocking request
template <class A>
inline void pop_ack_channel<A>::popReceive( )
{
    m_waiting = true;
    if (!m_active)
    {
        sc_core::wait(*m_channel_pop_event_ptr);
    }
    m_value_written = false;
    m_waiting = false;
}

// blocking read
template <class A>
inline void pop_ack_channel<A>::ack(const A& ack_ )
{
    interfaceBase::delay(false);
    m_active = false;
    m_ack_data = ack_;
    m_done = true;
    m_channel_ack_event.notify(SC_ZERO_TIME);
}

// blocking pop
template <class A>
inline void pop_ack_channel<A>::pop(  A& ack_, int magicValue  )
{
    // if we are reentering the write before the reader has had time to read the previous entry we need to block on the read event
    if (isLocking()) { synchLock_->lock(magicValue); }
    Q_ASSERT(m_multi_writer==false, "multiple threads driving interface, did you set multiwrite?");
    m_multi_writer = true;
    interfaceBase::delay(false);
    m_value_written = true;
    m_active = true;
    // for external arb case, we will not be in the read function so we need to unconditionally notify the event
    if (m_waiting || m_external_arb)
    {
        m_channel_pop_event_ptr->notify(SC_ZERO_TIME);
    }
    sc_core::wait(m_channel_ack_event);
    ack_ = m_ack_data;
    uint64_t tag = ack_.getStructValue();
    if (log_.isMatch(LOG_NORMAL)) {
        interfaceLog(ack_.prt(isDebugLog), tag);
    }
    m_multi_writer = false;
    if (isLocking()) { synchLock_->unlock(); }
}
// non-blocking variant for tee use case
template <class A>
inline void pop_ack_channel<A>::popNonBlocking( void )
{
    // if we are reentering the write before the reader has had time to read the previous entry we need to block on the read event
    Q_ASSERT(m_multi_writer==false, "multiple threads driving interface");
    m_multi_writer = true;
    interfaceBase::delay(false);
    m_value_written = true;
    m_active = true;
    m_done = false;
    // for external arb case, we will not be in the read function so we need to unconditionally notify the event
    if (m_waiting || m_external_arb)
    {
        m_channel_pop_event_ptr->notify(SC_ZERO_TIME);
    }
}
template <class A>
inline void pop_ack_channel<A>::waitAck( A& ack_ )
{
    if (!m_done) {
        sc_core::wait(m_channel_ack_event);
    }
    ack_ = m_ack_data;
    uint64_t tag = ack_.getStructValue();
    if (log_.isMatch(LOG_NORMAL)) {
        interfaceLog(ack_.prt(isDebugLog), tag);
    }

    m_multi_writer = false;
}

template <class A>
void pop_ack_channel<A>::status(void)
{
    if (m_value_written == true) {
        log_.logPrint(std::format("{} no ack received", name() ), LOG_IMPORTANT );
        dump();
    }
    teeStatus();
}

template <class A>
inline void pop_ack_channel<A>::trace( sc_trace_file* tf ) const
{
    (void) tf; /* ignore potentially unused parameter */
}


template <class A>
inline void pop_ack_channel<A>::print( ::std::ostream& os ) const
{
    os << m_ack_data.prt(isDebugLog) << '\n';
}

template <class A>
inline void pop_ack_channel<A>::dump( ::std::ostream& os ) const
{
    if (m_value_written)
    {
        os << m_ack_data.prt(isDebugLog) << '\n';
    } else {
        os << "no value" << '\n';
    }
}

template <class A>
inline ::std::ostream& operator << ( ::std::ostream& os, const pop_ack_channel<A>& a )
{
    a.print( os );
    return os;
}

} // namespace sc_core

template <class A>
using pop_ack_out = sc_port<pop_ack_out_if< A > >;
template <class A>
using pop_ack_in = sc_port<pop_ack_in_if<  A > >;

#endif // POP_BL_CHANNEL_H
