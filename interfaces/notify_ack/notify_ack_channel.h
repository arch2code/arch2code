// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef NOTIFY_ACK_CHANNEL_H
#define NOTIFY_ACK_CHANNEL_H

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

// notify( )
// |        -------> waitNotify( )
// |                     |
// |<--------------- ack( )

template <class T = bool>
class notify_ack_in_if
: virtual public sc_interface, virtual public portBase
{
public:

    // blocking read
    virtual void waitNotify( ) = 0;
    virtual void ack() = 0;
    virtual bool isActive() = 0;
    virtual bool isNotActive() = 0;
    virtual void setExternalEvent( sc_event *event ) = 0;

protected:
    // constructor
    notify_ack_in_if() {}

private:
    // disabled
    notify_ack_in_if( const notify_ack_in_if& );
    notify_ack_in_if& operator = ( const notify_ack_in_if& );
};
template <class T = bool>
class notify_ack_out_if
: virtual public sc_interface, virtual public portBase
{
public:
    // blocking write
    virtual void notify(int magicValue = 0) = 0;
    virtual void notifyNonBlocking(void) = 0;
    virtual void waitAck( void ) = 0;

protected:
    // constructor
    notify_ack_out_if() {}

private:
    // disabled
    notify_ack_out_if( const notify_ack_out_if& );
    notify_ack_out_if& operator = ( const notify_ack_out_if& );
};

template <class T = bool> // dummy template argument for consistency with other interfaces
class notify_ack_channel
: public notify_ack_in_if<T>,
  public notify_ack_out_if<T>,
  public sc_prim_channel,
  public interfaceBase
{
public:
    // constructor const char * module, std::string block
    explicit notify_ack_channel( const char* name_, std::string block_, INTERFACE_AUTO_MODE autoMode=INTERFACE_AUTO_OFF)
      : sc_prim_channel( name_ ),
        interfaceBase(name_, block_, autoMode),
        m_channel_notify_event( (std::string(name_) + "m_channel_notify_event").c_str() ),
        m_channel_ack_event( (std::string(name_) + "m_channel_ack_event").c_str() ),
        m_reader(nullptr),
        m_writer(nullptr),
        m_active(false),
        m_waiting(false),
        m_done(false)
        {
            logging::GetInstance().registerInterfaceStatus(std::string(name_), [this](void){ status();});
        }

    // destructor
    virtual ~notify_ack_channel() { }

    // interface methods
    virtual void register_port( sc_port_base&, const char* ) override;

    // blocking read
    virtual void waitNotify( void ) override;
    virtual void ack( void ) override;
    virtual bool isActive() override { return(m_active); }
    virtual bool isNotActive() override { return(!m_active); }

    // blocking notify
    virtual void notify(int magicValue = 0) override;
    virtual void notifyNonBlocking(void) override; //for tee use case only
    virtual void waitAck( void ) override; //for tee use case only

    void trace( sc_trace_file* tf ) const override;

    virtual void print( ::std::ostream& = ::std::cout ) const override;
    virtual void dump( ::std::ostream& = ::std::cout ) const override;
    virtual void status(void);

    virtual const char* kind() const override
        { return "notify_ack_channel"; }

    virtual void setExternalEvent( sc_event *event ) override
    {
        m_channel_notify_event_ptr = event;
        m_external_arb = true;
    }

    // portBase overrides
    void setMultiDriver(std::string name, std::function<std::string(const uint64_t &value)> prt = nullptr) override
    {
        interfaceBase::setMultiDriver(name, prt);
    }
    std::shared_ptr<trackerBase> getTracker(void) override { return (nullptr);}
    virtual void setTeeBusy(bool busy) override { teeBusy_ = busy; }
    virtual void setTandem(void) override { interfaceBase::setTandem(); }
    virtual void setLogging(verbosity_e verbosity) override { interfaceBase::setLogging(verbosity); }
    virtual void setTimed(int nsec, timedDelayMode mode) override { interfaceBase::setTimed(nsec, mode); }
    virtual sc_prim_channel* getChannel(void) override { return this; }

protected:
    sc_event m_channel_notify_event;
    sc_event* m_channel_notify_event_ptr;
    sc_event m_channel_ack_event;

    sc_port_base* m_reader; // used for static design rule checking
    sc_port_base* m_writer; // used for static design rule checking

    bool m_active = false;   // notify issued / waiting for ack
    bool m_waiting = false; // waiting for notify
    bool m_done = false; // done
    bool m_multi_writer = false; //detect multiple writers
    bool m_external_arb = false;

private:
    // disabled
    notify_ack_channel( const notify_ack_channel& );
    notify_ack_channel& operator = ( const notify_ack_channel& );
};

template <class T>
inline void notify_ack_channel<T>::register_port( sc_port_base& port_,
                const char* if_typename_ )
{
    std::string nm( if_typename_ );
    if( nm == typeid( notify_ack_in_if<T> ).name() )
    {
        // only one reader can be connected
        if( m_reader != 0 ) {
            SC_REPORT_ERROR( SC_ID_MORE_THAN_ONE_FIFO_READER_, 0 );
            // may continue, if suppressed
        }
        m_reader = &port_;
    } else if( nm == typeid( notify_ack_out_if<T> ).name() )
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
                         "notify_ack_channel<T> port not recognized" );
        // may continue, if suppressed
    }
}

// blocking waitNotify
template <class T>
inline void notify_ack_channel<T>::waitNotify( void )
{
    m_waiting = true;
    if (!m_active)
    {
        sc_core::wait(m_channel_notify_event);
    }
    m_waiting = false;
    if (log_.isMatch(LOG_NORMAL)) {
        interfaceLog("notify", 0);
    }
}

// blocking ack
template <class T>
inline void notify_ack_channel<T>::ack( )
{
    interfaceBase::delay(false);
    m_done = true;
    m_active = false;
    m_channel_ack_event.notify(SC_ZERO_TIME);
}


// blocking write
template <class T>
inline void notify_ack_channel<T>::notify(int magicValue)
{
    // if we are reentering the write before the reader has had time to read the previous entry we need to block on the read event
    if (isLocking()) { synchLock_->lock(magicValue); }
    Q_ASSERT(m_multi_writer==false, std::format("multiple threads driving {} interface, did you set multiwrite?", name() ));
    m_multi_writer = true;
    interfaceBase::delay(false);
    m_active = true;
    m_done = false;
    // for external arb case, we will not be in the read function so we need to unconditionally notify the event
    if (m_waiting || m_external_arb)
    {
        m_channel_notify_event.notify(SC_ZERO_TIME);
    }
    sc_core::wait(m_channel_ack_event);
    m_multi_writer = false;
    if (isLocking()) { synchLock_->unlock(); }
}


// non-blocking variant for tee use case only
template <class T>
inline void notify_ack_channel<T>::notifyNonBlocking(void)
{
    // if we are reentering the write before the reader has had time to read the previous entry we need to block on the read event
    Q_ASSERT(m_multi_writer==false, std::format("multiple threads driving {} interface", name() ));
    m_multi_writer = true;
    interfaceBase::delay(false);
    m_active = true;
    m_done = false;
    // for external arb case, we will not be in the read function so we need to unconditionally notify the event
    if (m_waiting || m_external_arb)
    {
        m_channel_notify_event.notify(SC_ZERO_TIME);
    }
}

// non-blocking variant for tee use case only
template <class T>
inline void notify_ack_channel<T>::waitAck( void )
{
    if (!m_done)
    {
        sc_core::wait(m_channel_ack_event);
    }
    m_multi_writer = false;
}


template <class T>
void notify_ack_channel<T>::status(void)
{
    if (m_active && !m_done)
    {
        log_.logPrint(std::format("{} notify issued but not ack", name()  ), LOG_IMPORTANT );
    }
    teeStatus();
}

template <class T>
inline void notify_ack_channel<T>::trace( sc_trace_file* tf ) const
{
    (void) tf; /* ignore potentially unused parameter */
}


template <class T>
inline void notify_ack_channel<T>::print( ::std::ostream& os ) const
{
    if (m_active && !m_done)
    {
        os << "notified" << '\n';
    }
}

template <class T>
inline void notify_ack_channel<T>::dump( ::std::ostream& os ) const
{
    if (m_active && !m_done)
    {
        os << "notified" << '\n';
    }
}

template <class T>
inline ::std::ostream& operator << ( ::std::ostream& os, const notify_ack_channel<T>& a )
{
    a.print( os );
    return os;
}

} // namespace sc_core

template <class T=bool>
using notify_ack_out = sc_port<notify_ack_out_if< T > >;
template <class T=bool>
using notify_ack_in = sc_port<notify_ack_in_if< T > >;

#endif // NOTIFY_ACK_CHANNEL_H
