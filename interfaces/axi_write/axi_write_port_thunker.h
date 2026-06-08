// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef AXI_WRITE_PORT_THUNKER_H
#define AXI_WRITE_PORT_THUNKER_H

#include "axi_write_channel.h"
#include "../../common/systemc/bitTwiddling.h"
#include "sysc/kernel/sc_dynamic_processes.h"
#include <optional>
#include <string>

// axi_write_port_thunker
//
// Header-only forwarding adapter held as a member of a generated container
// class. Bridges an upstream axi_write consumer-side endpoint carrying
// (axiWriteAddressSt<UpA>, axiWriteDataSt<UpD, UpS>) and the upstream
// response axiWriteRespSt to a downstream axi_write consumer port carrying
// (axiWriteAddressSt<DownA>, axiWriteDataSt<DownD, DownS>) and the
// downstream response axiWriteRespSt, when the corresponding payload
// structures are per-field _bitWidth equivalent but differ in nested
// _packedSt width. The per-field equivalence is validated elsewhere; this
// class performs the runtime packed-value bridge for the per-parameter
// envelope fields via copy_packed_bits() and preserves the AXI write
// address / data / response handshake at both ends.
//
// Up always denotes the parent side and Down the owned child channel; this
// is a topological position, not a data-flow direction (the producer shape
// below flows Down -> Up).
//
// Single-beat semantics only: the forwarding loop pulls one address, one
// data beat and one response per iteration. Multi-beat burst transfers
// and partial writes are out of scope for the thunker; the packed-form
// check is the canonical guard against width disagreement for the wrapped
// envelope.
//
// The fourth and fifth payload structs of the axi_write view are the
// strobe types (UpS / DownS). axi_write_if.yaml lists three struct
// parameters per side (addr_t, data_t, strb_t), so the template parameter
// list carries six types — three per side — matching the buildThunkerView
// enumeration order.
//
// Three construction shapes are supported. The first two are consumer-side
// (the downstream child end is an axi_write consumer,
// axi_write_in<DownA, DownD, DownS>&); the third is producer-side (the
// downstream child end is an axi_write producer,
// axi_write_out<DownA, DownD, DownS>&):
//   * connectionMap shape — the up side is a parent port
//     (axi_write_in<UpA, UpD, UpS>&). The port's bound interface is not
//     available until SystemC elaboration completes, so it is resolved
//     lazily on the first iteration of thunkIn().
//   * connections shape — the up side is the parent-side channel,
//     bound directly to its axi_write_in_if<UpA, UpD, UpS> interface
//     base. The channel is fully constructed before the thunker is, so
//     the interface pointer is captured immediately.
//   * producer (out) shape — the downstream child end is a producer
//     port (axi_write_out<DownA, DownD, DownS>&) that drives the owned
//     channel; the thunker consumes from the owned channel and drives the
//     bridged payload onto the parent-side channel's
//     axi_write_out_if<UpA, UpD, UpS>. Data flows child -> parent here,
//     the reverse of the consumer shapes. Used when a parameterized
//     producer instance feeds a non-parameterized container channel.
//
// In every shape the child-side port bind to the owned channel must occur
// during SystemC elaboration; that bind is performed in the constructor
// body (which is only reached when the thunker is held as a container
// member).
template <class UpA, class UpD, class UpS,
          class DownA, class DownD, class DownS>
class axi_write_port_thunker
{
public:
    // connectionMap shape: parent port reference.
    axi_write_port_thunker( const char* name_,
                            axi_write_in<UpA, UpD, UpS>&     upPort,
                            axi_write_in<DownA, DownD, DownS>& downPort,
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
    axi_write_port_thunker( const char* name_,
                            axi_write_in_if<UpA, UpD, UpS>&    upInIface,
                            axi_write_in<DownA, DownD, DownS>& downPort,
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
    // the parent-side channel's axi_write_out_if<UpA, UpD, UpS>.
    axi_write_port_thunker( const char* name_,
                            axi_write_out_if<UpA, UpD, UpS>&   upOutIface,
                            axi_write_out<DownA, DownD, DownS>& downPort,
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
        axi_write_in_if<UpA, UpD, UpS>* upIn =
            m_up_in_iface ? m_up_in_iface : m_up_port->operator->();
        while (true) {
            // Address phase: upstream receives, downstream sends.
            axiWriteAddressSt<UpA>   addrIn;
            axiWriteAddressSt<DownA> addrOut;
            typename axiWriteAddressSt<UpA>::_packedSt addrPacked;
            typename axiWriteAddressSt<DownA>::_packedSt addrOutPacked;
            upIn->receiveAddr( addrIn );
            // Generated payload structs expose pack() via an out
            // parameter (`void pack(_packedSt& _ret) const`).
            addrIn.pack( addrPacked );
            copy_packed_bits( addrOutPacked, addrPacked, axiWriteAddressSt<DownA>::_bitWidth );
            addrOut.unpack( addrOutPacked );
            // The channel's overridden sendAddr() drops the default
            // optional argument, so the std::nullopt is supplied
            // explicitly to satisfy the two-argument signature.
            m_down_channel.sendAddr( addrOut, std::nullopt );

            // Data phase: upstream receives, downstream sends.
            axiWriteDataSt<UpD, UpS>     dataIn;
            axiWriteDataSt<DownD, DownS> dataOut;
            typename axiWriteDataSt<UpD, UpS>::_packedSt dataPacked;
            typename axiWriteDataSt<DownD, DownS>::_packedSt dataOutPacked;
            upIn->receiveData( dataIn );
            dataIn.pack( dataPacked );
            copy_packed_bits( dataOutPacked, dataPacked, axiWriteDataSt<DownD, DownS>::_bitWidth );
            dataOut.unpack( dataOutPacked );
            m_down_channel.sendData( dataOut );

            // Response phase: downstream returns, upstream answered.
            axiWriteRespSt respIn;
            axiWriteRespSt respOut;
            typename axiWriteRespSt::_packedSt respPacked;
            typename axiWriteRespSt::_packedSt respOutPacked;
            m_down_channel.receiveResp( respIn );
            respIn.pack( respPacked );
            copy_packed_bits( respOutPacked, respPacked, axiWriteRespSt::_bitWidth );
            respOut.unpack( respOutPacked );
            upIn->sendResp( respOut );
        }
    }

    void thunkOut()
    {
        // Producer (out) shape: the child producer drives DownA/DownD into
        // the owned m_down_channel; bridge each payload and drive UpA/UpD
        // onto the parent-side channel. Mirrors thunkIn() with the consumer
        // object (upIn) replaced by m_down_channel, the producer object
        // (m_down_channel) replaced by m_up_out_iface, and every Up<->Down
        // type swapped.
        while (true) {
            // Address phase: downstream receives, upstream sends.
            axiWriteAddressSt<DownA> addrIn;
            axiWriteAddressSt<UpA>   addrOut;
            typename axiWriteAddressSt<DownA>::_packedSt addrPacked;
            typename axiWriteAddressSt<UpA>::_packedSt addrOutPacked;
            m_down_channel.receiveAddr( addrIn );
            // Generated payload structs expose pack() via an out
            // parameter (`void pack(_packedSt& _ret) const`).
            addrIn.pack( addrPacked );
            copy_packed_bits( addrOutPacked, addrPacked, axiWriteAddressSt<UpA>::_bitWidth );
            addrOut.unpack( addrOutPacked );
            // The out interface's sendAddr() carries a default optional
            // argument; the std::nullopt is supplied explicitly to mirror
            // thunkIn() and the channel's two-argument signature.
            m_up_out_iface->sendAddr( addrOut, std::nullopt );

            // Data phase: downstream receives, upstream sends.
            axiWriteDataSt<DownD, DownS> dataIn;
            axiWriteDataSt<UpD, UpS>     dataOut;
            typename axiWriteDataSt<DownD, DownS>::_packedSt dataPacked;
            typename axiWriteDataSt<UpD, UpS>::_packedSt dataOutPacked;
            m_down_channel.receiveData( dataIn );
            dataIn.pack( dataPacked );
            copy_packed_bits( dataOutPacked, dataPacked, axiWriteDataSt<UpD, UpS>::_bitWidth );
            dataOut.unpack( dataOutPacked );
            m_up_out_iface->sendData( dataOut );

            // Response phase: upstream returns, downstream answered.
            axiWriteRespSt respIn;
            axiWriteRespSt respOut;
            typename axiWriteRespSt::_packedSt respPacked;
            typename axiWriteRespSt::_packedSt respOutPacked;
            m_up_out_iface->receiveResp( respIn );
            respIn.pack( respPacked );
            copy_packed_bits( respOutPacked, respPacked, axiWriteRespSt::_bitWidth );
            respOut.unpack( respOutPacked );
            m_down_channel.sendResp( respOut );
        }
    }

    axi_write_in<UpA, UpD, UpS>*    m_up_port;
    axi_write_in_if<UpA, UpD, UpS>* m_up_in_iface;
    axi_write_out_if<UpA, UpD, UpS>* m_up_out_iface;
    axi_write_channel<DownA, DownD, DownS> m_down_channel;
};

#endif // AXI_WRITE_PORT_THUNKER_H
