// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef RDY_VLD_PORT_THUNKER_H
#define RDY_VLD_PORT_THUNKER_H

#include "../../common/systemc/bitTwiddling.h"
#include "rdy_vld_channel.h"
#include "sysc/kernel/sc_dynamic_processes.h"
#include <string>

// rdy_vld_port_thunker
//
// Header-only forwarding adapter held as a member of a generated container
// class. Bridges an upstream rdy_vld consumer-side endpoint carrying UpT to
// a downstream rdy_vld consumer port carrying DownT, when the two types are
// per-field _bitWidth equivalent but differ in nested _packedSt width. The
// per-field equivalence is validated elsewhere; this class performs the
// runtime packed-value bridge via copy_packed_bits().
//
// Up always denotes the parent side and Down the owned child channel; this
// is a topological position, not a data-flow direction (the producer shape
// below flows Down -> Up).
//
// Four construction shapes are supported, spanning a 2x2 family: the child
// (down) end is either a consumer (rdy_vld_in<DownT>&) or a producer
// (rdy_vld_out<DownT>&), and the parent (up) end is either a fully-bound
// channel interface base (captured eagerly) or an unbound parent port
// (resolved lazily on the spawned thread's first iteration, since the port's
// interface is not available until SystemC elaboration completes):
//   * connectionMap shape (consumer child, up port) — up is a parent port
//     rdy_vld_in<UpT>&, resolved lazily in thunkIn().
//   * connections shape (consumer child, up channel) — up is the parent-side
//     channel bound directly by its rdy_vld_in_if<UpT> interface base,
//     captured immediately.
//   * producer (out) shape (producer child, up channel) — the child producer
//     port rdy_vld_out<DownT>& writes into the owned channel; the thunker
//     reads from it and writes the bridged payload onto the parent-side
//     channel's rdy_vld_out_if<UpT>, captured immediately. Data flows
//     child -> parent, the reverse of the consumer shapes.
//   * producer (out) port shape (producer child, up port) — as the producer
//     shape, but the up side is an unbound parent port rdy_vld_out<UpT>&
//     (e.g. a testbench External's inherited <DUT>Inverted boundary port),
//     resolved lazily in thunkOut(). Used when a parameterized producer
//     instance feeds a non-parameterized boundary at an excluded-instance
//     (tb/DUT) boundary.
//
// In every shape the child-side port bind to the owned channel must occur
// during SystemC elaboration; that bind is performed in the constructor
// body (which is only reached when the thunker is held as a container
// member).
template <class UpT, class DownT>
class rdy_vld_port_thunker
{
public:
    // connectionMap shape: parent port reference.
    rdy_vld_port_thunker( const char* name_,
                          rdy_vld_in<UpT>&   upPort,
                          rdy_vld_in<DownT>& downPort,
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
    rdy_vld_port_thunker( const char* name_,
                          rdy_vld_in_if<UpT>& upInIface,
                          rdy_vld_in<DownT>&           downPort,
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
    // that writes into the owned channel; the bridged payload is written
    // onto the parent-side channel's rdy_vld_out_if<UpT>.
    rdy_vld_port_thunker( const char* name_,
                          rdy_vld_out_if<UpT>& upOutIface,
                          rdy_vld_out<DownT>&           downPort,
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
    // (rdy_vld_out<UpT>&), resolved lazily in thunkOut() once its interface
    // binds during elaboration. Mirrors the connectionMap shape's lazy port
    // handling for the producer direction.
    rdy_vld_port_thunker( const char* name_,
                          rdy_vld_out<UpT>&   upPort,
                          rdy_vld_out<DownT>& downPort,
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
        rdy_vld_in_if<UpT>* upIn =
            m_up_in_iface ? m_up_in_iface : m_up_port->operator->();
        while (true) {
            UpT   inVal;
            DownT outVal;
            typename UpT::_packedSt inPacked;
            typename DownT::_packedSt outPacked;
            upIn->readClocked( inVal );
            // Generated payload structs expose pack() via an out
            // parameter (`void pack(_packedSt& _ret) const`).
            inVal.pack( inPacked );
            copy_packed_bits( outPacked, inPacked, DownT::_bitWidth );
            outVal.unpack( outPacked );
            m_down_channel.writeClocked( outVal );
        }
    }

    void thunkOut()
    {
        // Producer (out) shape: the child producer writes DownT into the
        // owned m_down_channel; bridge each payload and write UpT onto the
        // parent-side channel, mirroring thunkIn() with the data flowing
        // child -> parent. Resolve the up-side interface once, from the eager
        // channel iface or (port shape) the lazily-bound parent out port.
        rdy_vld_out_if<UpT>* upOut =
            m_up_out_iface ? m_up_out_iface : m_up_out_port->operator->();
        while (true) {
            DownT inVal;
            UpT   outVal;
            typename DownT::_packedSt inPacked;
            typename UpT::_packedSt   outPacked;
            m_down_channel.readClocked( inVal );
            // Generated payload structs expose pack() via an out
            // parameter (`void pack(_packedSt& _ret) const`).
            inVal.pack( inPacked );
            copy_packed_bits( outPacked, inPacked, UpT::_bitWidth );
            outVal.unpack( outPacked );
            upOut->writeClocked( outVal );
        }
    }

    rdy_vld_in<UpT>*                m_up_port;
    rdy_vld_in_if<UpT>*    m_up_in_iface;
    rdy_vld_out_if<UpT>*   m_up_out_iface;
    rdy_vld_out<UpT>*      m_up_out_port;
    rdy_vld_channel<DownT> m_down_channel;
};

#endif // RDY_VLD_PORT_THUNKER_H
