// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef AXI_WRITE_PORT_THUNKER_H
#define AXI_WRITE_PORT_THUNKER_H

#include "axi_write_channel.h"
#include "../../common/systemc/bitTwiddling.h"
#include "sysc/kernel/sc_dynamic_processes.h"
#include <optional>
#include <string>
#include <type_traits>

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
// Four construction shapes are supported, spanning a 2x2 family: the child
// (down) end is either a consumer (axi_write_in<DownA, DownD, DownS>&) or a
// producer (axi_write_out<DownA, DownD, DownS>&), and the parent (up) end is
// either a fully-bound channel interface base (captured eagerly) or an
// unbound parent port (resolved lazily on the spawned thread's first
// iteration, since the port's interface is not available until SystemC
// elaboration completes):
//   * connectionMap shape (consumer child, up port) — up is a parent port
//     axi_write_in<UpA, UpD, UpS>&, resolved lazily in thunkIn().
//   * connections shape (consumer child, up channel) — up is the parent-side
//     channel bound directly by its axi_write_in_if<UpA, UpD, UpS> interface
//     base, captured immediately.
//   * producer (out) shape (producer child, up channel) — the child producer
//     port axi_write_out<DownA, DownD, DownS>& drives the owned channel; the
//     thunker consumes from it and drives the bridged payload onto the
//     parent-side channel's axi_write_out_if<UpA, UpD, UpS>, captured
//     immediately. Data flows child -> parent, the reverse of the consumer
//     shapes.
//   * producer (out) port shape (producer child, up port) — as the producer
//     shape, but the up side is an unbound parent port
//     axi_write_out<UpA, UpD, UpS>& (e.g. a testbench External's inherited
//     <DUT>Inverted boundary port), resolved lazily in thunkOut(). Used when
//     a parameterized producer instance feeds a non-parameterized boundary at
//     an excluded-instance (tb/DUT) boundary.
//
// In every shape the child-side port bind to the owned channel must occur
// during SystemC elaboration; that bind is performed in the constructor
// body (which is only reached when the thunker is held as a container
// member).
// UpID/UpIDW and DownID/DownIDW are not convertible across widths, so both
// ends of a bind must carry the same id_t: a transaction ID has to round-trip
// unchanged. Template argument order matches the generator
// (pysrc/intf_gen_utils.py _thunker_member_type): up-required, down-required,
// up-optional (in interface_defs order: AWU, WU, BU, ID/IDW), down-optional
// (AWU, WU, BU, ID/IDW).
template <class UpA, class UpD, class UpS,
          class DownA, class DownD, class DownS,
          class UpAWU = std::monostate, class UpWU = std::monostate, class UpBU = std::monostate, class UpID = _axiIdT, unsigned UpIDW = 4,
          class DownAWU = std::monostate, class DownWU = std::monostate, class DownBU = std::monostate, class DownID = _axiIdT, unsigned DownIDW = 4>
class axi_write_port_thunker
{
    static_assert(std::is_same_v<UpID, DownID> && UpIDW == DownIDW, "a cross-interface bind must carry the same id_t on both ends");
public:
    // connectionMap shape: parent port reference.
    axi_write_port_thunker( const char* name_,
                            axi_write_in<UpA, UpD, UpS, UpAWU, UpWU, UpBU, UpID, UpIDW>&     upPort,
                            axi_write_in<DownA, DownD, DownS, DownAWU, DownWU, DownBU, DownID, DownIDW>& downPort,
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
    axi_write_port_thunker( const char* name_,
                            axi_write_in_if<UpA, UpD, UpS, UpAWU, UpWU, UpBU, UpID, UpIDW>&    upInIface,
                            axi_write_in<DownA, DownD, DownS, DownAWU, DownWU, DownBU, DownID, DownIDW>& downPort,
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
    // that drives the owned channel; the bridged payload is driven onto
    // the parent-side channel's axi_write_out_if<UpA, UpD, UpS>.
    axi_write_port_thunker( const char* name_,
                            axi_write_out_if<UpA, UpD, UpS, UpAWU, UpWU, UpBU, UpID, UpIDW>&   upOutIface,
                            axi_write_out<DownA, DownD, DownS, DownAWU, DownWU, DownBU, DownID, DownIDW>& downPort,
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

    // producer (out) port shape: the up side is an unbound parent port
    // axi_write_out<UpA, UpD, UpS>& (e.g. a testbench External's inherited
    // <DUT>Inverted boundary port), resolved lazily in thunkOut(). Used when
    // a parameterized producer instance feeds a non-parameterized boundary at
    // an excluded-instance (tb/DUT) boundary.
    axi_write_port_thunker( const char* name_,
                            axi_write_out<UpA, UpD, UpS, UpAWU, UpWU, UpBU, UpID, UpIDW>&     upPort,
                            axi_write_out<DownA, DownD, DownS, DownAWU, DownWU, DownBU, DownID, DownIDW>& downPort,
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
        axi_write_in_if<UpA, UpD, UpS, UpAWU, UpWU, UpBU, UpID, UpIDW>* upIn =
            m_up_in_iface ? m_up_in_iface : m_up_port->operator->();
        while (true) {
            // Address phase: upstream receives, downstream sends.
            axiWriteAddressSt<UpA, UpAWU, UpID, UpIDW>   addrIn;
            axiWriteAddressSt<DownA, DownAWU, DownID, DownIDW> addrOut;
            typename axiWriteAddressSt<UpA, UpAWU, UpID, UpIDW>::_packedSt addrPacked;
            typename axiWriteAddressSt<DownA, DownAWU, DownID, DownIDW>::_packedSt addrOutPacked;
            upIn->receiveAddr( addrIn );
            // Generated payload structs expose pack() via an out
            // parameter (`void pack(_packedSt& _ret) const`).
            addrIn.pack( addrPacked );
            copy_packed_bits( addrOutPacked, addrPacked, axiWriteAddressSt<DownA, DownAWU, DownID, DownIDW>::_bitWidth );
            addrOut.unpack( addrOutPacked );
            // The channel's overridden sendAddr() drops the default
            // optional argument, so the std::nullopt is supplied
            // explicitly to satisfy the two-argument signature.
            m_down_channel.sendAddr( addrOut, std::nullopt );

            // Data phase: upstream receives, downstream sends.
            axiWriteDataSt<UpD, UpS, UpWU, UpID, UpIDW>     dataIn;
            axiWriteDataSt<DownD, DownS, DownWU, DownID, DownIDW> dataOut;
            typename axiWriteDataSt<UpD, UpS, UpWU, UpID, UpIDW>::_packedSt dataPacked;
            typename axiWriteDataSt<DownD, DownS, DownWU, DownID, DownIDW>::_packedSt dataOutPacked;
            upIn->receiveData( dataIn );
            dataIn.pack( dataPacked );
            copy_packed_bits( dataOutPacked, dataPacked, axiWriteDataSt<DownD, DownS, DownWU, DownID, DownIDW>::_bitWidth );
            dataOut.unpack( dataOutPacked );
            m_down_channel.sendData( dataOut );

            // Response phase: downstream returns, upstream answered.
            axiWriteRespSt<DownBU, DownID, DownIDW> respIn;
            axiWriteRespSt<UpBU, UpID, UpIDW>   respOut;
            typename axiWriteRespSt<DownBU, DownID, DownIDW>::_packedSt respPacked;
            typename axiWriteRespSt<UpBU, UpID, UpIDW>::_packedSt   respOutPacked;
            m_down_channel.receiveResp( respIn );
            respIn.pack( respPacked );
            copy_packed_bits( respOutPacked, respPacked, axiWriteRespSt<UpBU, UpID, UpIDW>::_bitWidth );
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
        // type swapped. Resolve the up-side interface once, from the eager
        // channel iface or (port shape) the lazily-bound parent out port.
        axi_write_out_if<UpA, UpD, UpS, UpAWU, UpWU, UpBU, UpID, UpIDW>* upOut =
            m_up_out_iface ? m_up_out_iface : m_up_out_port->operator->();
        while (true) {
            // Address phase: downstream receives, upstream sends.
            axiWriteAddressSt<DownA, DownAWU, DownID, DownIDW> addrIn;
            axiWriteAddressSt<UpA, UpAWU, UpID, UpIDW>   addrOut;
            typename axiWriteAddressSt<DownA, DownAWU, DownID, DownIDW>::_packedSt addrPacked;
            typename axiWriteAddressSt<UpA, UpAWU, UpID, UpIDW>::_packedSt addrOutPacked;
            m_down_channel.receiveAddr( addrIn );
            // Generated payload structs expose pack() via an out
            // parameter (`void pack(_packedSt& _ret) const`).
            addrIn.pack( addrPacked );
            copy_packed_bits( addrOutPacked, addrPacked, axiWriteAddressSt<UpA, UpAWU, UpID, UpIDW>::_bitWidth );
            addrOut.unpack( addrOutPacked );
            // The out interface's sendAddr() carries a default optional
            // argument; the std::nullopt is supplied explicitly to mirror
            // thunkIn() and the channel's two-argument signature.
            upOut->sendAddr( addrOut, std::nullopt );

            // Data phase: downstream receives, upstream sends.
            axiWriteDataSt<DownD, DownS, DownWU, DownID, DownIDW> dataIn;
            axiWriteDataSt<UpD, UpS, UpWU, UpID, UpIDW>     dataOut;
            typename axiWriteDataSt<DownD, DownS, DownWU, DownID, DownIDW>::_packedSt dataPacked;
            typename axiWriteDataSt<UpD, UpS, UpWU, UpID, UpIDW>::_packedSt dataOutPacked;
            m_down_channel.receiveData( dataIn );
            dataIn.pack( dataPacked );
            copy_packed_bits( dataOutPacked, dataPacked, axiWriteDataSt<UpD, UpS, UpWU, UpID, UpIDW>::_bitWidth );
            dataOut.unpack( dataOutPacked );
            upOut->sendData( dataOut );

            // Response phase: upstream returns, downstream answered.
            axiWriteRespSt<UpBU, UpID, UpIDW>   respIn;
            axiWriteRespSt<DownBU, DownID, DownIDW> respOut;
            typename axiWriteRespSt<UpBU, UpID, UpIDW>::_packedSt   respPacked;
            typename axiWriteRespSt<DownBU, DownID, DownIDW>::_packedSt respOutPacked;
            upOut->receiveResp( respIn );
            respIn.pack( respPacked );
            copy_packed_bits( respOutPacked, respPacked, axiWriteRespSt<DownBU, DownID, DownIDW>::_bitWidth );
            respOut.unpack( respOutPacked );
            m_down_channel.sendResp( respOut );
        }
    }

    axi_write_in<UpA, UpD, UpS, UpAWU, UpWU, UpBU, UpID, UpIDW>*    m_up_port;
    axi_write_in_if<UpA, UpD, UpS, UpAWU, UpWU, UpBU, UpID, UpIDW>* m_up_in_iface;
    axi_write_out_if<UpA, UpD, UpS, UpAWU, UpWU, UpBU, UpID, UpIDW>* m_up_out_iface;
    axi_write_out<UpA, UpD, UpS, UpAWU, UpWU, UpBU, UpID, UpIDW>* m_up_out_port;
    axi_write_channel<DownA, DownD, DownS, DownAWU, DownWU, DownBU, DownID, DownIDW> m_down_channel;
};

#endif // AXI_WRITE_PORT_THUNKER_H
