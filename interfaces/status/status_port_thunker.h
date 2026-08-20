// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef STATUS_PORT_THUNKER_H
#define STATUS_PORT_THUNKER_H

#include "../../common/systemc/bitTwiddling.h"
#include "status_channel.h"
#include "sysc/kernel/sc_dynamic_processes.h"
#include <string>

// status_port_thunker
//
// Header-only forwarding adapter held as a member of a generated container
// class. Bridges an upstream status consumer-side endpoint carrying UpT to a
// downstream status consumer port carrying DownT, when the two types are
// per-field _bitWidth equivalent but differ in nested _packedSt width.
// Per-field equivalence is validated elsewhere; this class performs the
// runtime payload bridge via copyPayload() and republishes each observed
// value onto the other side.
//
// DirectData is the generator's verdict for the one payload pair this protocol
// carries (data_t): true when the two declarations emit identical member
// storage, which lets copyPayload() transfer the value whole instead of packing
// and unpacking it field by field. It defaults to false, which is always
// correct and merely slower, so a hand-written instantiation need not supply it.
//
// status is a published-value protocol rather than a handshake: write() is
// non-blocking and suppresses a repeat of the value already published, and
// read() blocks on the next update. The bridge therefore republishes on each
// observed update and inherits both properties — a bridged value that equals
// the one already published on the far side is dropped there, exactly as it
// would be without the adapter.
//
// Up always denotes the parent side and Down the owned child channel; this
// is a topological position, not a data-flow direction (the producer shape
// below flows Down -> Up).
//
// Four construction shapes are supported, spanning a 2x2 family: the child
// (down) end is either a consumer (status_in<DownT>&) or a producer
// (status_out<DownT>&), and the parent (up) end is either a fully-bound
// channel interface base (captured eagerly) or an unbound parent port
// (resolved lazily on the spawned thread's first iteration, since the port's
// interface is not available until SystemC elaboration completes):
//   * connectionMap shape (consumer child, up port) — up is a parent port
//     status_in<UpT>&, resolved lazily in thunkIn().
//   * connections shape (consumer child, up channel) — up is the parent-side
//     channel bound directly by its status_in_if<UpT> interface base,
//     captured immediately.
//   * producer (out) shape (producer child, up channel) — the child producer
//     port status_out<DownT>& publishes into the owned channel; the thunker
//     observes it and publishes the bridged value onto the parent-side
//     channel's status_out_if<UpT>, captured immediately. Data flows
//     child -> parent, the reverse of the consumer shapes.
//   * producer (out) port shape (producer child, up port) — as the producer
//     shape, but the up side is an unbound parent port status_out<UpT>&
//     (e.g. a testbench External's inherited <DUT>Inverted boundary port),
//     resolved lazily in thunkOut(). Used when a parameterized producer
//     instance feeds a non-parameterized boundary at an excluded-instance
//     (tb/DUT) boundary.
//
// In every shape the child-side port bind to the owned channel must occur
// during SystemC elaboration; that bind is performed in the constructor
// body (which is only reached when the thunker is held as a container
// member). The overloaded constructors are disambiguated by the child
// end's port type (status_in vs status_out), so the container generator
// emits identical wiring for both directions.
template <class UpT, class DownT, bool DirectData = false>
class status_port_thunker
{
public:
    // connectionMap shape: parent port reference.
    status_port_thunker( const char* name_,
                         status_in<UpT>&   upPort,
                         status_in<DownT>& downPort,
                         std::string block_ )
      : m_up_port( &upPort ),
        m_up_in_iface( nullptr ),
        m_up_out_iface( nullptr ),
        m_up_out_port( nullptr ),
        m_down_channel( (std::string(name_) + "_ch").c_str(), block_, m_down_initial )
    {
        downPort( m_down_channel );
        sc_core::sc_spawn( [this]() { this->thunkIn(); } );
    }

    // connections shape: parent-side channel bound by its interface base.
    status_port_thunker( const char* name_,
                         status_in_if<UpT>& upInIface,
                         status_in<DownT>&  downPort,
                         std::string block_ )
      : m_up_port( nullptr ),
        m_up_in_iface( &upInIface ),
        m_up_out_iface( nullptr ),
        m_up_out_port( nullptr ),
        m_down_channel( (std::string(name_) + "_ch").c_str(), block_, m_down_initial )
    {
        downPort( m_down_channel );
        sc_core::sc_spawn( [this]() { this->thunkIn(); } );
    }

    // producer (out) shape: the downstream child end is a producer port
    // that publishes into the owned channel; the bridged value is published
    // onto the parent-side channel's status_out_if<UpT>.
    status_port_thunker( const char* name_,
                         status_out_if<UpT>& upOutIface,
                         status_out<DownT>&  downPort,
                         std::string block_ )
      : m_up_port( nullptr ),
        m_up_in_iface( nullptr ),
        m_up_out_iface( &upOutIface ),
        m_up_out_port( nullptr ),
        m_down_channel( (std::string(name_) + "_ch").c_str(), block_, m_down_initial )
    {
        downPort( m_down_channel );
        sc_core::sc_spawn( [this]() { this->thunkOut(); } );
    }

    // producer (out) port shape: the up side is an unbound parent OUT port
    // (status_out<UpT>&), resolved lazily in thunkOut() once its interface
    // binds during elaboration. Mirrors the connectionMap shape's lazy port
    // handling for the producer direction.
    status_port_thunker( const char* name_,
                         status_out<UpT>&   upPort,
                         status_out<DownT>& downPort,
                         std::string block_ )
      : m_up_port( nullptr ),
        m_up_in_iface( nullptr ),
        m_up_out_iface( nullptr ),
        m_up_out_port( &upPort ),
        m_down_channel( (std::string(name_) + "_ch").c_str(), block_, m_down_initial )
    {
        downPort( m_down_channel );
        sc_core::sc_spawn( [this]() { this->thunkOut(); } );
    }

private:
    void thunkIn()
    {
        // Resolve the up-side interface once. For the port shape, sc_port
        // binding is complete by the time the spawned thread first runs.
        status_in_if<UpT>* upIn =
            m_up_in_iface ? m_up_in_iface : m_up_port->operator->();
        while (true) {
            UpT   inVal;
            DownT outVal;
            upIn->read( inVal );
            static_assert( !DirectData || sizeof(DownT) == sizeof(UpT), "status data_t direct copy requires equal payload size" );
            copyPayload<DirectData>( outVal, inVal );
            m_down_channel.write( outVal );
        }
    }

    void thunkOut()
    {
        // Producer (out) shape: the child producer publishes DownT into the
        // owned m_down_channel; bridge each update and publish UpT onto the
        // parent-side channel, mirroring thunkIn() with the data flowing
        // child -> parent. Resolve the up-side interface once, from the eager
        // channel iface or (port shape) the lazily-bound parent out port.
        status_out_if<UpT>* upOut =
            m_up_out_iface ? m_up_out_iface : m_up_out_port->operator->();
        while (true) {
            DownT inVal;
            UpT   outVal;
            m_down_channel.read( inVal );
            static_assert( !DirectData || sizeof(UpT) == sizeof(DownT), "status data_t direct copy requires equal payload size" );
            copyPayload<DirectData>( outVal, inVal );
            upOut->write( outVal );
        }
    }

    status_in<UpT>*      m_up_port;
    status_in_if<UpT>*   m_up_in_iface;
    status_out_if<UpT>*  m_up_out_iface;
    status_out<UpT>*     m_up_out_port;
    // status_channel's initial-value parameter defaults to
    // `typename T::_packedSt(0)`, which is not a valid expression when the
    // packed form is a word array, so the owned channel is always handed an
    // explicit zero. Declared before m_down_channel so it is initialized first.
    //
    // The owned channel therefore starts at zero rather than at the connection's
    // declared default: the emitted adapter constructor call is fixed at four
    // arguments and carries no initial value, so a register-backed status
    // connection's default_value cannot reach it. Only a reader that samples
    // before the first update can observe the difference, and readNonBlocking()
    // has no caller anywhere in the tree today.
    typename DownT::_packedSt m_down_initial{};
    status_channel<DownT> m_down_channel;
};

#endif // STATUS_PORT_THUNKER_H
