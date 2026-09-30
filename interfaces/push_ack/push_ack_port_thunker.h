// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef PUSH_ACK_PORT_THUNKER_H
#define PUSH_ACK_PORT_THUNKER_H

#include "../../common/systemc/bitTwiddling.h"
#include "push_ack_channel.h"
#include "sysc/kernel/sc_dynamic_processes.h"
#include <cstdint>
#include <string>

// push_ack_port_thunker
//
// Header-only forwarding adapter held as a member of a generated container
// class. Bridges an upstream push_ack consumer-side endpoint carrying UpT
// to a downstream push_ack consumer port carrying DownT, when the two
// types are per-field _bitWidth equivalent but differ in nested _packedSt
// width. Per-field equivalence is validated elsewhere; this class performs
// the runtime payload bridge via copyPayload() and preserves the
// push_ack request / acknowledge handshake at both ends.
//
// DirectData is the generator's verdict for the one payload pair this protocol
// carries (data_t): true when the two declarations emit identical member
// storage, which lets copyPayload() transfer the value whole instead of packing
// and unpacking it field by field. It defaults to false, which is always
// correct and merely slower, so a hand-written instantiation need not supply it.
//
// Up always denotes the parent side and Down the owned child channel; this
// is a topological position, not a data-flow direction (the producer shape
// below flows Down -> Up).
//
// Four construction shapes are supported, spanning a 2x2 family: the child
// (down) end is either a consumer (push_ack_in<DownT>&) or a producer
// (push_ack_out<DownT>&), and the parent (up) end is either a fully-bound
// channel interface base (captured eagerly) or an unbound parent port
// (resolved lazily on the spawned thread's first iteration, since the port's
// interface is not available until SystemC elaboration completes):
//   * connectionMap shape (consumer child, up port) — up is a parent port
//     push_ack_in<UpT>&, resolved lazily in thunkIn().
//   * connections shape (consumer child, up channel) — up is the parent-side
//     channel bound directly by its push_ack_in_if<UpT> interface base,
//     captured immediately.
//   * producer (out) shape (producer child, up channel) — the child producer
//     port push_ack_out<DownT>& pushes into the owned channel; the thunker
//     consumes from it and pushes the bridged payload onto the parent-side
//     channel's push_ack_out_if<UpT>, captured immediately. Data flows
//     child -> parent, the reverse of the consumer shapes.
//   * producer (out) port shape (producer child, up port) — as the producer
//     shape, but the up side is an unbound parent port push_ack_out<UpT>&
//     (e.g. a testbench External's inherited <DUT>Inverted boundary port),
//     resolved lazily in thunkOut(). Used when a parameterized producer
//     instance feeds a non-parameterized boundary at an excluded-instance
//     (tb/DUT) boundary.
//
// In every shape the child-side port bind to the owned channel must occur
// during SystemC elaboration; that bind is performed in the constructor
// body (which is only reached when the thunker is held as a container
// member). The overloaded constructors are disambiguated by the child
// end's port type (push_ack_in vs push_ack_out), so the container
// generator emits identical wiring for both directions.
template <class UpT, class DownT, bool DirectData = false>
class push_ack_port_thunker
{
public:
    // connectionMap shape: parent port reference.
    push_ack_port_thunker( const char* name_,
                           push_ack_in<UpT>&   upPort,
                           push_ack_in<DownT>& downPort,
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
    push_ack_port_thunker( const char* name_,
                           push_ack_in_if<UpT>& upInIface,
                           push_ack_in<DownT>&           downPort,
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
    // that pushes into the owned channel; the bridged payload is pushed
    // onto the parent-side channel's push_ack_out_if<UpT>.
    push_ack_port_thunker( const char* name_,
                           push_ack_out_if<UpT>& upOutIface,
                           push_ack_out<DownT>&           downPort,
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
    // (push_ack_out<UpT>&), resolved lazily in thunkOut() once its interface
    // binds during elaboration. Mirrors the connectionMap shape's lazy port
    // handling for the producer direction.
    push_ack_port_thunker( const char* name_,
                           push_ack_out<UpT>&   upPort,
                           push_ack_out<DownT>& downPort,
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
        push_ack_in_if<UpT>* upIn =
            m_up_in_iface ? m_up_in_iface : m_up_port->operator->();
        while (true) {
            UpT   inVal;
            DownT outVal;
            upIn->pushReceive( inVal );
            static_assert( !DirectData || sizeof(DownT) == sizeof(UpT), "push_ack data_t direct copy requires equal payload size" );
            copyPayload<DirectData>( outVal, inVal );
            // push() drives the downstream handshake; the concrete
            // push_ack_channel<T>::push override has no default argument,
            // so the magic value is passed explicitly here.
            m_down_channel.push( outVal, (uint64_t)-1 );
            upIn->ack();
        }
    }

    void thunkOut()
    {
        // Producer (out) shape: the child producer pushes DownT into the
        // owned m_down_channel; bridge each payload and push UpT onto the
        // parent-side channel. Acking the child only after the parent push
        // completes preserves end-to-end backpressure, mirroring thunkIn().
        // Resolve the up-side interface once, from the eager channel iface or
        // (port shape) the lazily-bound parent out port.
        push_ack_out_if<UpT>* upOut =
            m_up_out_iface ? m_up_out_iface : m_up_out_port->operator->();
        while (true) {
            DownT inVal;
            UpT   outVal;
            m_down_channel.pushReceive( inVal );
            static_assert( !DirectData || sizeof(UpT) == sizeof(DownT), "push_ack data_t direct copy requires equal payload size" );
            copyPayload<DirectData>( outVal, inVal );
            upOut->push( outVal, (uint64_t)-1 );
            m_down_channel.ack();
        }
    }

    push_ack_in<UpT>*                m_up_port;
    push_ack_in_if<UpT>*    m_up_in_iface;
    push_ack_out_if<UpT>*   m_up_out_iface;
    push_ack_out<UpT>*      m_up_out_port;
    push_ack_channel<DownT> m_down_channel;
};

#endif // PUSH_ACK_PORT_THUNKER_H
