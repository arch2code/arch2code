// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef STATUS_CHANNEL_H
#define STATUS_CHANNEL_H

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
class status_in_if
: virtual public sc_interface, virtual public portBase
{
public:

    // blocking read
    virtual void read( T& ) = 0;
    virtual T read() = 0;
    // non-blocking variant
    virtual void readNonBlocking( T& ) = 0;
    virtual T readNonBlocking() = 0;
    virtual void setExternalEvent( sc_event *event ) = 0;

protected:
    // constructor
    status_in_if() {}

private:
    // disabled
    status_in_if( const status_in_if<T>& );
    status_in_if<T>& operator = ( const status_in_if<T>& );
};

template <class T>
class status_out_if
: virtual public sc_interface, virtual public portBase
{
public:
    // non-blocking
    virtual void write( const T& val_ ) = 0;

protected:
    // constructor
    status_out_if() {}

private:
    // disabled
    status_out_if( const status_out_if<T>& );
    status_out_if<T>& operator = ( const status_out_if<T>& );
};

template <class T>
class status_channel
: public status_in_if<T>,
  public status_out_if<T>,
  public sc_prim_channel,
  public interfaceBase
{
public:
    // constructor const char * module, std::string block
    explicit status_channel( const char* name_, std::string block_,
                             INTERFACE_AUTO_MODE autoMode,
                             const typename T::_packedSt& initialValue)
      : sc_prim_channel( name_ ),
        interfaceBase(name_, block_, autoMode),
        m_channel_update_event( (std::string(name_) + "m_channel_update_event").c_str() ),
        m_channel_update_event_ptr(&m_channel_update_event),
        m_reader(nullptr),
        m_writer(nullptr)
        {
            setTracker(T::getValueType());
            logging::GetInstance().registerInterfaceStatus(std::string(name_), [this](void){ status();});
            m_value.unpack(initialValue);
        }

    explicit status_channel( const char* name_, std::string block_,
        const typename T::_packedSt& initialValue = typename T::_packedSt(0) )
      : status_channel(name_, block_, INTERFACE_AUTO_OFF, initialValue)
        {
        }

    // destructor
    virtual ~status_channel() {}

    // interface methods
    virtual void register_port( sc_port_base&, const char* ) override;

    // blocking push
    virtual void read( T& ) override;
    virtual T read() override;
    // non-blocking variant
    virtual void readNonBlocking( T& ) override;
    virtual T readNonBlocking() override;
    virtual void setExternalEvent( sc_event *event ) override
    {
        m_channel_update_event_ptr = event;
        m_external_arb = true;
    }
    // non-blocking variant
    virtual void write( const T& val_ ) override;
    // other methods
    operator T ()
        { return read(); }

    status_channel<T>& operator = ( const T& a )
        { write( a ); return *this; }

    void trace( sc_trace_file* tf ) const override;

    virtual void print( ::std::ostream& = ::std::cout ) const override;
    virtual void dump( ::std::ostream& = ::std::cout ) const override;
    virtual void status(void);

    virtual const char* kind() const override
        { return "status_channel"; }

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

    sc_event m_channel_update_event;
    sc_event* m_channel_update_event_ptr;

    sc_port_base* m_reader; // used for static design rule checking
    sc_port_base* m_writer; // used for static design rule checking

    bool m_value_written = false; // m_value contain valid data when true
    bool m_external_arb = false;

private:
    // disabled
    status_channel( const status_channel<T>& );
    status_channel& operator = ( const status_channel<T>& );
};

template <class T>
inline void status_channel<T>::register_port( sc_port_base& port_,
                const char* if_typename_ )
{
    std::string nm( if_typename_ );
    if( nm == typeid( status_in_if<T> ).name() )
    {
        // multiple readers can be connected 
        if( m_reader == 0 ) {
            m_reader = &port_;
	}
    } else if( nm == typeid( status_out_if<T> ).name() )
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
                         "status_channel<T> port not recognized" );
        // may continue, if suppressed
    }
}

// blocking read
template <class T>
inline void status_channel<T>::read( T& val_ )
{
    wait(*m_channel_update_event_ptr);
    val_ = m_value;
}


template <class T>
inline T status_channel<T>::read()
{
    wait(*m_channel_update_event_ptr);
    return m_value;
}

// non-blocking write
template <class T>
inline void status_channel<T>::write( const T& val_ )
{
    if (m_value_written && val_ == m_value ) {
        return;
    }
    m_value_written = true;
    interfaceBase::delay(false);
    m_value = val_;
    m_channel_update_event_ptr->notify(SC_ZERO_TIME);
}


// non-blocking read
template <class T>
inline void status_channel<T>::readNonBlocking( T& val_ )
{
    val_ = m_value;
}

template <class T>
inline T status_channel<T>::readNonBlocking( )
{
    return m_value;
}

template <class T>
void status_channel<T>::status(void)
{
    // for status interface there is nothing to print by default
    teeStatus();
}

template <class T>
inline void status_channel<T>::trace( sc_trace_file* tf ) const
{
    (void) tf; /* ignore potentially unused parameter */
}


template <class T>
inline void status_channel<T>::print( ::std::ostream& os ) const
{
    os << m_value.prt(isDebugLog) << '\n';
}

template <class T>
inline void status_channel<T>::dump( ::std::ostream& os ) const
{
    if (m_value_written)
    {
        os << m_value.prt(isDebugLog) << '\n';
    } else {
        os << "no value" << '\n';
    }
}

template <class T>
inline ::std::ostream& operator << ( ::std::ostream& os, const status_channel<T>& a )
{
    a.print( os );
    return os;
}

} // namespace sc_core

template <class T>
using status_out = sc_port<status_out_if< T > >;
template <class T>
using status_in = sc_port<status_in_if< T > >;

#endif // STATUS_CHANNEL_H
