//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsStat
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: uvmRegsStat
module uvmRegsStat
// Generated Import package statement(s)
import uvmRegs_package::*;
#(
    parameter int unsigned UVM_REGS_TAB_W = 32'h0000_000C
)
(
    rdy_vld_if.dst in,
    apb_if.dst apbReg,
    rdy_vld_if.src out,
    input clk, rst_n
);

    // Module-local parameterizable type/struct declarations
    typedef logic[UVM_REGS_TAB_W-1:0] uvmRegsTabT; //Tab row
    typedef struct packed {
        uvmRegsTabT entry; //XORed into each word whose low bits select the row
    } uvmRegsTabSt;

    // Interface Instances, needed for between instanced modules inside this module
    status_if #(.data_t(uvmRegsModeSt)) mode();
    status_if #(.data_t(uvmRegsCountSt)) count();
    external_reg_if #(.data_t(uvmRegsScratchSt)) scratch();
    memory_if #(.data_t(uvmRegsTabSt), .addr_t(uvmRegsIdxSt)) tab();

    // Memory Interfaces
    memory_if #(.data_t(uvmRegsWordSt), .addr_t(uvmRegsIdxSt)) hist_reg();
    memory_if #(.data_t(uvmRegsWordSt), .addr_t(uvmRegsIdxSt)) hist();

// Instances
uvmRegsStat_regs #(.UVM_REGS_TAB_W(UVM_REGS_TAB_W)) u_uvmRegsStat_regs (
    .apbReg (apbReg),
    .hist (hist_reg),
    .mode (mode),
    .count (count),
    .scratch (scratch),
    .tab (tab),
    .clk (clk),
    .rst_n (rst_n)
);

// Memory Instances
memory_dp #(.DEPTH(UVM_REGS_TAB_ROWS), .data_t(uvmRegsWordSt), .PORTA_READ_ONLY(1'b1), .PORTB_WRITE_ONLY(1'b1)) uHist (
    .mem_portA (hist_reg),
    .mem_portB (hist),
    .clk (clk)
);

// GENERATED_CODE_END

    // tab's rows, served to the register handler with a one-clock read.
    typedef uvmRegsTabSt [UVM_REGS_TAB_ROWS-1:0] uvmRegsTabRowsT;
    `DFF_INST(uvmRegsTabRowsT, tabRows)
    `DFF_INST(uvmRegsTabSt, tabRead)
    always_comb begin
        n_tabRows = tabRows;
        n_tabRead = tabRead;
        if (tab.enable && tab.wr_en) begin
            n_tabRows[tab.addr.idx] = tab.write_data;
        end else if (tab.enable) begin
            n_tabRead = tabRows[tab.addr.idx];
        end
    end
    assign tab.read_data = tabRead;

    `DFF_INST(uvmRegsScratchSt, scratchValue)
    assign n_scratchValue = (|scratch.write) ? scratch.wdata : scratchValue;
    assign scratch.rdata = scratchValue;

    logic        take;
    uvmRegsIdxT  idx;
    uvmRegsWordT mixed;
    assign take = in.vld && out.rdy;
    assign idx = uvmRegsIdxT'(in.data.word);
    assign mixed = in.data.word ^ uvmRegsWordT'(tabRows[idx].entry);
    assign out.vld = in.vld;
    assign in.rdy = out.rdy;
    assign out.data.word = mode.data.invert ? ~mixed : mixed;

    `DFF_INST(uvmRegsWordT, words)
    assign n_words = take ? words + 1'b1 : words;
    assign count.data.count = words;

    assign hist.enable = take;
    assign hist.wr_en = take;
    assign hist.addr.idx = idx;
    assign hist.write_data = in.data;

endmodule: uvmRegsStat
