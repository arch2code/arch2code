// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef PUSH_ACK_CHANNEL_H
#define PUSH_ACK_CHANNEL_H

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

// write(T)
// |        ---T---> read(T)

template <class T>
class raw_in_if
: virtual public sc_interface, virtual public portBase
{
public:

    // blocking read
    virtual void read( T& ) = 0;
    virtual T read() = 0;
    virtual void setExternalEvent( sc_event *event ) = 0;

protected:
    // constructor
    raw_in_if() {}

private:
    // disabled
    raw_in_if( const raw_in_if<T>& );
    raw_in_if<T>& operator = ( const raw_in_if<T>& );
};

template <class T>
class raw_out_if
: virtual public sc_interface, virtual public portBase
{
public:
    // blocking write
    virtual void write( const T&, uint64_t userMagic = (uint64_t)-1 ) = 0;

protected:
    // constructor
    raw_out_if() {}

private:
    // disabled
    raw_out_if( const raw_out_if<T>& );
    raw_out_if<T>& operator = ( const raw_out_if<T>& );
};

template <class T>
class raw_channel
: public raw_in_if<T>,
  public raw_out_if<T>,
  public sc_prim_channel,
  public interfaceBase
{
public:
    // constructor const char * module, std::string block
    explicit raw_channel( const char* name_, std::string block_, INTERFACE_AUTO_MODE autoMode=INTERFACE_AUTO_OFF)
      : sc_prim_channel( name_ ),
        interfaceBase(name_, block_, autoMode),
        m_channel_sync_event( (std::string(name_) + "m_channel_sync_event").c_str() ),
        m_channel_sync_event_ptr(&m_channel_sync_event),
        m_reader(nullptr),
        m_writer(nullptr),
        m_waiting(false),
        m_value_written(false)
        {
            setTracker(T::getValueType());
            logging::GetInstance().registerInterfaceStatus(std::string(name_), [this](void){ status();});
        }

    // destructor
    virtual ~raw_channel() {}

    // interface methods
    virtual void register_port( sc_port_base&, const char* ) override;

    // blocking push
    virtual void read( T& ) override;
    virtual T read() override;
    virtual void setExternalEvent( sc_event *event ) override
    {
        m_channel_sync_event_ptr = event;
        m_external_arb = true;
    }
    // blocking push
    virtual void write( const T&, uint64_t userMagic ) override;
    // other methods
    operator T ()
        { return read(); }

    raw_channel<T>& operator = ( const T& a )
        { write( a ); return *this; }

    void trace( sc_trace_file* tf ) const override;

    virtual void print( ::std::ostream& = ::std::cout ) const override;
    virtual void dump( ::std::ostream& = ::std::cout ) const override;
    virtual void status(void);

    virtual const char* kind() const override
        { return "raw_channel"; }

    // portBase overrides
    void setMultiDriver(std::string name, std::function<std::string(const uint64_t &value)> prt = nullptr) override
    {
        interfaceBase::setMultiDriver(name, prt);
    }
    std::shared_ptr<trackerBase> getTracker(void) override { return (tracker_);}
    virtual void setTeeBusy(bool busy) override { teeBusy_ = busy; }
    virtual void setTandem(void) override { interfaceBase::setTandem(); }
    virtual void setLogging(verbosity_e verbosity) override { interfaceBase::setLogging(verbosity); }
    virtual void setTimed(int nsec, timedDelayMode mode) override { interfaceBase::setTimed(nsec, mode); }
    virtual sc_prim_channel* getChannel(void) override { return this; }

protected:
    T    m_value;           // the data

    sc_event m_channel_sync_event;
    sc_event* m_channel_sync_event_ptr;

    sc_port_base* m_reader; // used for static design rule checking
    sc_port_base* m_writer; // used for static design rule checking

    bool m_waiting = false; // waiting for write
    bool m_value_written = false; // m_value contain valid data when true
    bool m_multi_writer = false; //detect multiple writers
    bool m_external_arb = false;

private:
    // disabled
    raw_channel( const raw_channel<T>& );
    raw_channel& operator = ( const raw_channel<T>& );
};

template <class T>
inline void raw_channel<T>::register_port( sc_port_base& port_,
                const char* if_typename_ )
{
    std::string nm( if_typename_ );
    if( nm == typeid( raw_in_if<T> ).name() )
    {
        // only one reader can be connected
        if( m_reader != 0 ) {
            SC_REPORT_ERROR( SC_ID_MORE_THAN_ONE_FIFO_READER_, 0 );
            // may continue, if suppressed
        }
        m_reader = &port_;
    } else if( nm == typeid( raw_out_if<T> ).name() )
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
                         "raw_channel<T> port not recognized" );
        // may continue, if suppressed
    }
}

// blocking read
template <class T>
inline void raw_channel<T>::read( T& val_ )
{
    m_waiting = true;
    // as the event maybe external and probably shared in this case, we cannot guarentee that the event is for us
    while (!m_value_written) {
        sc_core::wait(*m_channel_sync_event_ptr);
    }
    val_ = m_value;
    m_value_written = false;
    m_waiting = false;
    uint64_t tag = val_.getStructValue();
    if (log_.isMatch(LOG_NORMAL)) {
        interfaceLog(val_.prt(isDebugLog), tag);
    }
    m_channel_sync_event_ptr->notify(SC_ZERO_TIME);
}


template <class T>
inline T raw_channel<T>::read()
{
    T tmp;
    read( tmp );
    return tmp;
}

// blocking write
template <class T>
inline void raw_channel<T>::write( const T& val_, uint64_t userMagic )
{
    // if we are reentering the write before the reader has had time to read the previous entry we need to block on the read event
    if (isLocking())
    {
        uint64_t magicValue = userMagic;
        if (magicValue == (uint64_t)-1)
        {
            magicValue = val_.getStructValue();
            if (magicValue == (uint64_t)-1) {
                typename T::_packedSt packed;
                val_.pack(packed);
                magicValue = fnv1a_hash((uint8_t *)&packed, T::_byteWidth);
            }
        }
        synchLock_->lock(magicValue);
    }

    Q_ASSERT(m_multi_writer==false, "multiple threads driving interface, did you set multiwrite?");
    m_multi_writer = true;
    interfaceBase::delay(false);
    m_value_written = true;
    m_value = val_;
    // for external arb case, we will not be in the read function so we need to unconditionally notify the event
    if (m_waiting || m_external_arb)
    {
        m_channel_sync_event_ptr->notify(SC_ZERO_TIME);
    }
    sc_core::wait(m_channel_sync_event);
    m_multi_writer = false;
    if (isLocking()) { synchLock_->unlock(); }
}

template <class T>
void raw_channel<T>::status(void)
{
    if (m_value_written == true)
    {
        log_.logPrint(std::format("{} has data/or no ack received", name()  ), LOG_IMPORTANT );
        dump();
    }
    teeStatus();
}

template <class T>
inline void raw_channel<T>::trace( sc_trace_file* tf ) const
{
    (void) tf; /* ignore potentially unused parameter */
}


template <class T>
inline void raw_channel<T>::print( ::std::ostream& os ) const
{
    os << m_value.prt(isDebugLog) << '\n';
}

template <class T>
inline void raw_channel<T>::dump( ::std::ostream& os ) const
{
    if (m_value_written)
    {
        os << m_value.prt(isDebugLog) << '\n';
    } else {
        os << "no value" << '\n';
    }
}
template <>
inline void raw_channel<bool>::dump( ::std::ostream& os ) const
{
    if (m_value_written)
    {
        os << m_value << '\n';
    } else {
        os << "no value" << '\n';
    }
}

template <class T>
inline ::std::ostream& operator << ( ::std::ostream& os, const raw_channel<T>& a )
{
    a.print( os );
    return os;
}

} // namespace sc_core

template <class T>
using raw_out = sc_port<raw_out_if< T > >;
template <class T>
using raw_in = sc_port<raw_in_if< T > >;

#endif // PUSH_ACK_CHANNEL_H
