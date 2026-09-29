// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef POP_ACK_PORT_THUNKER_H
#define POP_ACK_PORT_THUNKER_H

#include "../../common/systemc/bitTwiddling.h"
#include "pop_ack_channel.h"
#include "sysc/kernel/sc_dynamic_processes.h"
#include <string>

// pop_ack_port_thunker
//
// Header-only forwarding adapter held as a member of a generated container
// class. Bridges an upstream pop_ack consumer-side endpoint carrying UpT to
// a downstream pop_ack consumer port carrying DownT, when the two types are
// per-field _bitWidth equivalent but differ in nested _packedSt width.
// Per-field equivalence is validated elsewhere; this class performs the
// runtime payload bridge via copyPayload() and preserves the pop_ack
// pop / acknowledge handshake at both ends.
//
// DirectRdata is the generator's verdict for the one payload pair this
// protocol carries (rdata_t): true when the two declarations emit identical
// member storage, which lets copyPayload() transfer the value whole instead of
// packing and unpacking it field by field. It defaults to false, which is
// always correct and merely slower, so a hand-written instantiation need not
// supply it.
//
// pop_ack carries its payload on the acknowledge rather than on the request:
// the requester pops and the completer answers with rdata_t. The bridged value
// therefore travels opposite to the pop, in both construction shapes.
//
// Up always denotes the parent side and Down the owned child channel; this
// is a topological position, not a data-flow direction.
//
// Four construction shapes are supported, spanning a 2x2 family: the child
// (down) end is either a consumer (pop_ack_in<DownT>&) or a producer
// (pop_ack_out<DownT>&), and the parent (up) end is either a fully-bound
// channel interface base (captured eagerly) or an unbound parent port
// (resolved lazily on the spawned thread's first iteration, since the port's
// interface is not available until SystemC elaboration completes):
//   * connectionMap shape (consumer child, up port) — up is a parent port
//     pop_ack_in<UpT>&, resolved lazily in thunkIn().
//   * connections shape (consumer child, up channel) — up is the parent-side
//     channel bound directly by its pop_ack_in_if<UpT> interface base,
//     captured immediately.
//   * producer (out) shape (producer child, up channel) — the child producer
//     port pop_ack_out<DownT>& pops from the owned channel; the thunker
//     receives that pop and issues it onto the parent-side channel's
//     pop_ack_out_if<UpT>, acknowledging the child with the bridged answer.
//   * producer (out) port shape (producer child, up port) — as the producer
//     shape, but the up side is an unbound parent port pop_ack_out<UpT>&
//     (e.g. a testbench External's inherited <DUT>Inverted boundary port),
//     resolved lazily in thunkOut(). Used when a parameterized producer
//     instance feeds a non-parameterized boundary at an excluded-instance
//     (tb/DUT) boundary.
//
// In every shape the child-side port bind to the owned channel must occur
// during SystemC elaboration; that bind is performed in the constructor
// body (which is only reached when the thunker is held as a container
// member). The overloaded constructors are disambiguated by the child
// end's port type (pop_ack_in vs pop_ack_out), so the container generator
// emits identical wiring for both directions.
template <class UpT, class DownT, bool DirectRdata = false>
class pop_ack_port_thunker
{
public:
    // connectionMap shape: parent port reference.
    pop_ack_port_thunker( const char* name_,
                          pop_ack_in<UpT>&   upPort,
                          pop_ack_in<DownT>& downPort,
                          std::string block_ )
      : m_up_port( &upPort ),
        m_up_in_iface( nullptr ),
        m_up_out_iface( nullptr ),
        m_up_out_port( nullptr ),
        m_down_channel( (std::string(name_) + "_ch").c_str(), block_ )
    {
        downPort( m_down_channel );
        sc_core::sc_spawn( [this]() { this->thunkIn(); } );
    }

    // connections shape: parent-side channel bound by its interface base.
    pop_ack_port_thunker( const char* name_,
                          pop_ack_in_if<UpT>& upInIface,
                          pop_ack_in<DownT>&  downPort,
                          std::string block_ )
      : m_up_port( nullptr ),
        m_up_in_iface( &upInIface ),
        m_up_out_iface( nullptr ),
        m_up_out_port( nullptr ),
        m_down_channel( (std::string(name_) + "_ch").c_str(), block_ )
    {
        downPort( m_down_channel );
        sc_core::sc_spawn( [this]() { this->thunkIn(); } );
    }

    // producer (out) shape: the downstream child end is a producer port
    // that pops from the owned channel; the bridged pop is issued onto the
    // parent-side channel's pop_ack_out_if<UpT>.
    pop_ack_port_thunker( const char* name_,
                          pop_ack_out_if<UpT>& upOutIface,
                          pop_ack_out<DownT>&  downPort,
                          std::string block_ )
      : m_up_port( nullptr ),
        m_up_in_iface( nullptr ),
        m_up_out_iface( &upOutIface ),
        m_up_out_port( nullptr ),
        m_down_channel( (std::string(name_) + "_ch").c_str(), block_ )
    {
        downPort( m_down_channel );
        sc_core::sc_spawn( [this]() { this->thunkOut(); } );
    }

    // producer (out) port shape: the up side is an unbound parent OUT port
    // (pop_ack_out<UpT>&), resolved lazily in thunkOut() once its interface
    // binds during elaboration. Mirrors the connectionMap shape's lazy port
    // handling for the producer direction.
    pop_ack_port_thunker( const char* name_,
                          pop_ack_out<UpT>&   upPort,
                          pop_ack_out<DownT>& downPort,
                          std::string block_ )
      : m_up_port( nullptr ),
        m_up_in_iface( nullptr ),
        m_up_out_iface( nullptr ),
        m_up_out_port( &upPort ),
        m_down_channel( (std::string(name_) + "_ch").c_str(), block_ )
    {
        downPort( m_down_channel );
        sc_core::sc_spawn( [this]() { this->thunkOut(); } );
    }

private:
    void thunkIn()
    {
        // Resolve the up-side interface once. For the port shape, sc_port
        // binding is complete by the time the spawned thread first runs.
        pop_ack_in_if<UpT>* upIn =
            m_up_in_iface ? m_up_in_iface : m_up_port->operator->();
        while (true) {
            DownT inVal;
            UpT   outVal;
            // Accept the parent's pop, then pop the owned channel; the child
            // completer's answer is what the parent is acknowledged with, so
            // the parent's ack is deferred until the child has answered.
            upIn->popReceive();
            m_down_channel.pop( inVal );
            static_assert( !DirectRdata || sizeof(UpT) == sizeof(DownT), "pop_ack rdata_t direct copy requires equal payload size" );
            copyPayload<DirectRdata>( outVal, inVal );
            upIn->ack( outVal );
        }
    }

    void thunkOut()
    {
        // Producer (out) shape: the child requester pops the owned
        // m_down_channel; issue that pop onto the parent-side channel and
        // acknowledge the child with the bridged answer. This is thunkIn()
        // with the consumer and producer objects exchanged and every
        // Up<->Down type swapped. Resolve the up-side interface once, from
        // the eager channel iface or (port shape) the lazily-bound parent
        // out port.
        pop_ack_out_if<UpT>* upOut =
            m_up_out_iface ? m_up_out_iface : m_up_out_port->operator->();
        while (true) {
            UpT   inVal;
            DownT outVal;
            m_down_channel.popReceive();
            upOut->pop( inVal );
            static_assert( !DirectRdata || sizeof(DownT) == sizeof(UpT), "pop_ack rdata_t direct copy requires equal payload size" );
            copyPayload<DirectRdata>( outVal, inVal );
            m_down_channel.ack( outVal );
        }
    }

    pop_ack_in<UpT>*      m_up_port;
    pop_ack_in_if<UpT>*   m_up_in_iface;
    pop_ack_out_if<UpT>*  m_up_out_iface;
    pop_ack_out<UpT>*     m_up_out_port;
    pop_ack_channel<DownT> m_down_channel;
};

#endif // POP_ACK_PORT_THUNKER_H
