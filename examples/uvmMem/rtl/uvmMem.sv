//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmMem
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: uvmMem
module uvmMem
// Generated Import package statement(s)
import uvmMem_package::*;
(
    rdy_vld_if.dst cmd,
    rdy_vld_if.src out,
    memory_if.src wr,
    memory_if.src rd,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

// Instances
// GENERATED_CODE_END

    // One command at a time: read through rd, take the word on the next
    // clock, write the command's word through wr, and send the word read on
    // out. cmd is ready again only once out has taken the word.
    typedef enum logic [2:0] {IDLE, READ, CAPTURE, WRITE, SEND} stateT;
    `DFFR_INST(stateT, state, IDLE)
    `DFFEN_INST(uvmMemCmdSt, cmdReg, cmd.vld & cmd.rdy)
    `DFFEN_INST(uvmMemWordSt, word, state == CAPTURE)

    assign n_cmdReg = cmd.data;
    assign n_word = rd.read_data;

    always_comb begin
        n_state = state;
        cmd.rdy = 1'b0;
        out.vld = 1'b0;
        out.data = word;
        wr.enable = 1'b0;
        wr.wr_en = 1'b0;
        wr.addr = uvmMemAddrSt'(cmdReg.wrAddr);
        wr.write_data = uvmMemWordSt'(cmdReg.data);
        rd.enable = 1'b0;
        rd.wr_en = 1'b0;
        rd.addr = uvmMemAddrSt'(cmdReg.rdAddr);
        rd.write_data = '0;
        case (state)
            IDLE: begin
                cmd.rdy = 1'b1;
                if (cmd.vld) begin
                    n_state = READ;
                end
            end
            READ: begin
                rd.enable = 1'b1;
                n_state = CAPTURE;
            end
            CAPTURE: begin
                n_state = WRITE;
            end
            WRITE: begin
                wr.enable = 1'b1;
                wr.wr_en = 1'b1;
                n_state = SEND;
            end
            SEND: begin
                out.vld = 1'b1;
                if (out.rdy) begin
                    n_state = IDLE;
                end
            end
            default: begin
                `qAssertFatal($isunknown(state), "uvmMem: state is not a defined state")
                n_state = IDLE;
            end
        endcase
    end

endmodule: uvmMem
