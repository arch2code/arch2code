// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef EXTERNAL_REG_CHANNEL_H
#define EXTERNAL_REG_CHANNEL_H

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
// |        ---T---> reg_read(T) where transaction is change of value event
//
//                   reg_write(T)
// read(T) <---T---|
//
template <class T>
class external_reg_in_if
: virtual public sc_interface, virtual public portBase
{
public:

    // blocking read
    virtual void read( T& ) = 0;
    // non-blocking variant
    virtual void readNonBlocking( T& ) = 0;
    virtual T readNonBlocking() = 0;
    virtual void setExternalEvent( sc_event *event ) = 0;
    // non-blocking
    virtual void write( const T& val_ ) = 0;
    virtual void reg_write( const T& val_ ) = 0; // triggers event to reader

protected:
    // constructor
    external_reg_in_if() {}

private:
    // disabled
    external_reg_in_if( const external_reg_in_if<T>& );
    external_reg_in_if<T>& operator = ( const external_reg_in_if<T>& );
};

template <class T>
class external_reg_out_if
: virtual public sc_interface, virtual public portBase
{
public:
    // blocking read
    virtual void reg_read( T& ) = 0;             // waits on event
    virtual T reg_read() = 0;
    // blocking write
    virtual void write( const T& val_ ) = 0;
    virtual void reg_write( const T& val_ ) = 0; // triggers event to reader

protected:
    // constructor
    external_reg_out_if() {}

private:
    // disabled
    external_reg_out_if( const external_reg_out_if<T>& );
    external_reg_out_if<T>& operator = ( const external_reg_out_if<T>& );
};

template <class T>
class external_reg_channel
: public external_reg_in_if<T>,
  public external_reg_out_if<T>,
  public sc_prim_channel,
  public interfaceBase
{
public:
    // constructor const char * module, std::string block
    explicit external_reg_channel( const char* name_, std::string block_,
                                   INTERFACE_AUTO_MODE autoMode,
                                   const typename T::_packedSt& initialValue = typename T::_packedSt(0))
      : sc_prim_channel( name_ ),
        interfaceBase(name_, block_, autoMode),
        m_channel_update_event( (std::string(name_) + "m_channel_update_event").c_str() ),
        m_channel_update_event_ptr(&m_channel_update_event),
        m_reg_write_event( (std::string(name_) + "m_reg_write_event").c_str() ),
        m_reader(nullptr),
        m_writer(nullptr)
        {
            setTracker(T::getValueType());
            logging::GetInstance().registerInterfaceStatus(std::string(name_), [this](void){ status();});
            m_write_data.unpack(initialValue);
        }
    explicit external_reg_channel( const char* name_, std::string block_,
                                   const typename T::_packedSt& initialValue = typename T::_packedSt(0))
      : external_reg_channel(name_, block_, INTERFACE_AUTO_OFF, initialValue)
        {
        }

    // destructor
    virtual ~external_reg_channel() {}

    // interface methods
    virtual void register_port( sc_port_base&, const char* ) override;

    // blocking push
    virtual void read( T& ) override;
    // non-blocking variant
    virtual void readNonBlocking( T& ) override;
    virtual T readNonBlocking() override;
    virtual void setExternalEvent( sc_event *event ) override
    {
        m_channel_update_event_ptr = event;
        m_external_arb = true;
    }
    // non-blocking
    virtual void write( const T& val_ ) override;
    // blocking read
    virtual void reg_read( T& ) override;             // waits on event
    virtual T reg_read() override;             // waits on event
    // blocking write
    virtual void reg_write( const T& val_ ) override; // triggers event to reader
    // other methods
    operator T ()
        { return read(); }

    external_reg_channel<T>& operator = ( const T& a )
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
    T    m_status_value;           // the data
    T    m_write_data;

    sc_event m_channel_update_event;
    sc_event* m_channel_update_event_ptr;
    sc_event m_reg_write_event;

    sc_port_base* m_reader; // used for static design rule checking
    sc_port_base* m_writer; // used for static design rule checking

    bool m_status_value_written = false; // m_value contain valid data when true
    bool m_external_arb = false;

private:
    // disabled
    external_reg_channel( const external_reg_channel<T>& );
    external_reg_channel& operator = ( const external_reg_channel<T>& );
};

template <class T>
inline void external_reg_channel<T>::register_port( sc_port_base& port_,
                const char* if_typename_ )
{
    std::string nm( if_typename_ );
    if( nm == typeid( external_reg_in_if<T> ).name() )
    {
        // multiple readers can be connected
        if( m_reader == 0 ) {
            m_reader = &port_;
	}
    } else if( nm == typeid( external_reg_out_if<T> ).name() )
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
                         "external_reg_channel<T> port not recognized" );
        // may continue, if suppressed
    }
}

// blocking read
template <class T>
inline void external_reg_channel<T>::reg_read( T& val_ )
{
    wait(*m_channel_update_event_ptr);
    val_ = m_status_value;
}


template <class T>
inline T external_reg_channel<T>::reg_read()
{
    wait(*m_channel_update_event_ptr);
    return m_status_value;
}

// non-blocking write for status interface
template <class T>
inline void external_reg_channel<T>::write( const T& val_ )
{
    if (m_status_value_written && val_ == m_status_value ) {
        return;
    }
    m_status_value_written = true;
    interfaceBase::delay(false);
    m_status_value = val_;
    m_channel_update_event_ptr->notify(SC_ZERO_TIME);
}

template <class T>
inline void external_reg_channel<T>::reg_write( const T& val_ )
{
    m_write_data = val_;
    interfaceBase::delay(false);
    m_reg_write_event.notify(SC_ZERO_TIME);
}

template <class T>
inline void external_reg_channel<T>::read( T& val_ )
{
    wait(m_reg_write_event);
    val_ = m_write_data;
}

// non-blocking read
template <class T>
inline void external_reg_channel<T>::readNonBlocking( T& val_ )
{
    val_ = m_write_data;
}

template <class T>
inline T external_reg_channel<T>::readNonBlocking( )
{
    return m_write_data;
}

template <class T>
void external_reg_channel<T>::status(void)
{
    // for status interface there is nothing to print by default
    teeStatus();
}

template <class T>
inline void external_reg_channel<T>::trace( sc_trace_file* tf ) const
{
    (void) tf; /* ignore potentially unused parameter */
}


template <class T>
inline void external_reg_channel<T>::print( ::std::ostream& os ) const
{
    os << m_status_value.prt(isDebugLog) << '\n';
}

template <class T>
inline void external_reg_channel<T>::dump( ::std::ostream& os ) const
{
    if (m_status_value_written)
    {
        os << m_status_value.prt(isDebugLog) << '\n';
    } else {
        os << "no value" << '\n';
    }
}

template <class T>
inline ::std::ostream& operator << ( ::std::ostream& os, const external_reg_channel<T>& a )
{
    a.print( os );
    return os;
}

} // namespace sc_core

template <class T>
using external_reg_out = sc_port<external_reg_out_if< T > >;
template <class T>
using external_reg_in = sc_port<external_reg_in_if< T > >;

#endif // EXTERNAL_REG_CHANNEL_H
