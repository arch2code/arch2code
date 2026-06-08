// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef AXI_READ_PORT_THUNKER_H
#define AXI_READ_PORT_THUNKER_H

#include "axi_read_channel.h"
#include "../../common/systemc/bitTwiddling.h"
#include "sysc/kernel/sc_dynamic_processes.h"
#include <optional>
#include <string>

// axi_read_port_thunker
//
// Header-only forwarding adapter held as a member of a generated container
// class. Bridges an upstream axi_read consumer-side endpoint carrying
// (axiReadAddressSt<UpA>, axiReadRespSt<UpD>) to a downstream axi_read
// consumer port carrying (axiReadAddressSt<DownA>, axiReadRespSt<DownD>),
// when the two pairs are per-field _bitWidth equivalent but differ in
// nested _packedSt width. Per-field equivalence is validated elsewhere;
// this class performs the runtime packed-value bridge via copy_packed_bits()
// in both directions and preserves the AXI read handshake at both ends.
//
// Up always denotes the parent side and Down the owned child channel; this
// is a topological position, not a data-flow direction (the producer shape
// below flows Down -> Up).
//
// Single-beat semantics only: the forwarding loop pulls one address and
// returns one response per iteration. Multi-beat burst transfers are out
// of scope for the thunker; the packed-form check is the canonical guard
// against width disagreement for the wrapped envelope.
//
// Three construction shapes are supported. The first two are consumer-side
// (the downstream child end is an axi_read consumer, axi_read_in<DownA,
// DownD>&); the third is producer-side (the downstream child end is an
// axi_read producer, axi_read_out<DownA, DownD>&):
//   * connectionMap shape — the up side is a parent port
//     (axi_read_in<UpA, UpD>&). The port's bound interface is not
//     available until SystemC elaboration completes, so it is resolved
//     lazily on the first iteration of thunkIn().
//   * connections shape — the up side is the parent-side channel,
//     bound directly to its axi_read_in_if<UpA, UpD> interface base.
//     The channel is fully constructed before the thunker is, so the
//     interface pointer is captured immediately.
//   * producer (out) shape — the downstream child end is a producer port
//     (axi_read_out<DownA, DownD>&) that drives the owned channel; the
//     thunker consumes from the owned channel and drives the bridged
//     payload onto the parent-side channel's axi_read_out_if<UpA, UpD>.
//     Data flows child -> parent here, the reverse of the consumer
//     shapes. Used when a parameterized producer instance feeds a
//     non-parameterized container channel.
//
// In every shape the child-side port bind to the owned channel must occur
// during SystemC elaboration; that bind is performed in the constructor
// body (which is only reached when the thunker is held as a container
// member).
template <class UpA, class UpD, class DownA, class DownD>
class axi_read_port_thunker
{
public:
    // connectionMap shape: parent port reference.
    axi_read_port_thunker( const char* name_,
                           axi_read_in<UpA, UpD>&     upPort,
                           axi_read_in<DownA, DownD>& downPort,
                           std::string block_ )
      : m_up_port( &upPort ),
        m_up_in_iface( nullptr ),
        m_up_out_iface( nullptr ),
        m_down_channel( (std::string(name_) + "_ch").c_str(), block_ )
    {
        downPort( m_down_channel );
        sc_core::sc_spawn( [this]() { this->thunkIn(); } );
    }

    // connections shape: parent-side channel bound by its interface base.
    axi_read_port_thunker( const char* name_,
                           axi_read_in_if<UpA, UpD>&  upInIface,
                           axi_read_in<DownA, DownD>& downPort,
                           std::string block_ )
      : m_up_port( nullptr ),
        m_up_in_iface( &upInIface ),
        m_up_out_iface( nullptr ),
        m_down_channel( (std::string(name_) + "_ch").c_str(), block_ )
    {
        downPort( m_down_channel );
        sc_core::sc_spawn( [this]() { this->thunkIn(); } );
    }

    // producer (out) shape: the downstream child end is a producer port
    // that drives the owned channel; the bridged payload is driven onto
    // the parent-side channel's axi_read_out_if<UpA, UpD>.
    axi_read_port_thunker( const char* name_,
                           axi_read_out_if<UpA, UpD>&  upOutIface,
                           axi_read_out<DownA, DownD>& downPort,
                           std::string block_ )
      : m_up_port( nullptr ),
        m_up_in_iface( nullptr ),
        m_up_out_iface( &upOutIface ),
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
        axi_read_in_if<UpA, UpD>* upIn =
            m_up_in_iface ? m_up_in_iface : m_up_port->operator->();
        while (true) {
            // Address phase: upstream receives, downstream sends.
            axiReadAddressSt<UpA>   addrIn;
            axiReadAddressSt<DownA> addrOut;
            typename axiReadAddressSt<UpA>::_packedSt addrPacked;
            typename axiReadAddressSt<DownA>::_packedSt addrOutPacked;
            upIn->receiveAddr( addrIn );
            // Generated payload structs expose pack() via an out
            // parameter (`void pack(_packedSt& _ret) const`).
            addrIn.pack( addrPacked );
            copy_packed_bits( addrOutPacked, addrPacked, axiReadAddressSt<DownA>::_bitWidth );
            addrOut.unpack( addrOutPacked );
            // The channel's overridden sendAddr() drops the default
            // optional argument, so the std::nullopt is supplied
            // explicitly to satisfy the two-argument signature.
            m_down_channel.sendAddr( addrOut, std::nullopt );

            // Data phase: downstream returns, upstream answered.
            axiReadRespSt<DownD> dataIn;
            axiReadRespSt<UpD>   dataOut;
            typename axiReadRespSt<DownD>::_packedSt dataPacked;
            typename axiReadRespSt<UpD>::_packedSt   dataOutPacked;
            m_down_channel.receiveData( dataIn );
            dataIn.pack( dataPacked );
            copy_packed_bits( dataOutPacked, dataPacked, axiReadRespSt<UpD>::_bitWidth );
            dataOut.unpack( dataOutPacked );
            upIn->sendData( dataOut );
        }
    }

    void thunkOut()
    {
        // Producer (out) shape: the child producer drives DownA/DownD into
        // the owned m_down_channel; bridge each payload and drive UpA/UpD
        // onto the parent-side channel. Data flows child -> parent,
        // mirroring thunkIn() with every Up/Down role swapped.
        while (true) {
            // Address phase: downstream receives, upstream sends.
            axiReadAddressSt<DownA> addrIn;
            axiReadAddressSt<UpA>   addrOut;
            typename axiReadAddressSt<DownA>::_packedSt addrPacked;
            typename axiReadAddressSt<UpA>::_packedSt   addrOutPacked;
            m_down_channel.receiveAddr( addrIn );
            // Generated payload structs expose pack() via an out
            // parameter (`void pack(_packedSt& _ret) const`).
            addrIn.pack( addrPacked );
            copy_packed_bits( addrOutPacked, addrPacked, axiReadAddressSt<UpA>::_bitWidth );
            addrOut.unpack( addrOutPacked );
            // The out interface's sendAddr() carries a defaulted optional
            // argument; the std::nullopt is supplied explicitly to mirror
            // the channel-side call in thunkIn().
            m_up_out_iface->sendAddr( addrOut, std::nullopt );

            // Data phase: upstream returns, downstream answered.
            axiReadRespSt<UpD>   dataIn;
            axiReadRespSt<DownD> dataOut;
            typename axiReadRespSt<UpD>::_packedSt   dataPacked;
            typename axiReadRespSt<DownD>::_packedSt dataOutPacked;
            m_up_out_iface->receiveData( dataIn );
            dataIn.pack( dataPacked );
            copy_packed_bits( dataOutPacked, dataPacked, axiReadRespSt<DownD>::_bitWidth );
            dataOut.unpack( dataOutPacked );
            m_down_channel.sendData( dataOut );
        }
    }

    axi_read_in<UpA, UpD>*    m_up_port;
    axi_read_in_if<UpA, UpD>* m_up_in_iface;
    axi_read_out_if<UpA, UpD>* m_up_out_iface;
    axi_read_channel<DownA, DownD> m_down_channel;
};

#endif // AXI_READ_PORT_THUNKER_H
