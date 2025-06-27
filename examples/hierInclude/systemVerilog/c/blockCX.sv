// GENERATED_CODE_PARAM --block=blockCX --importPackage=hierIncludeCInclude_package
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: blockCX
module blockCX
// Generated Import package statement(s)
import hierInclude_package::*;
import hierIncludeC_package::*;
// User supplied Import package statement(s)
import hierIncludeCInclude_package::*;
(
    rdy_vld_if.src cx2y,
    rdy_vld_if.src cx2z,
    rdy_vld_if.dst anInterface,
    req_ack_if.dst b2C,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

// Instances

// GENERATED_CODE_END


// at hierInclude yaml context
//    hierIncludePackage.sv
yetAnotherSizeT yet;
aBiggerT a2;
aSt a;

integer i;
always_comb begin
    yet             = '1;
    a2              = '0;
    a.variablea2[0] = a2;
    a.yetAnother    = yet;
    anInterface.rdy = 1'b1;
    if (anInterface.vld) begin
        a.variablea = anInterface.data.variablea;
        a.another   = anInterface.data.another;
        for(i=1; i<ASIZE2; i++) begin
            a.variablea2[i] = '1;
        end
    end
end


// at hierIncludeC yaml context
//    hierIncludeCPackage.sv
cSt c;
always_ff @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        c <= '0;
    end else if (cx2z.rdy) begin
        c <= c + 1'b1;
    end
end
always_comb begin
    cx2z.vld     = 1'b1;
    cx2z.data = c;
end

// at hierIncludeCInclude yaml context
//    hierIncludeCIncludePackage.sv
cStateT cState;
dT d;
dSt secondD;
dSt thirdD;

logic ack;
assign b2C.ack = ack;

always_ff @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        cState  <= '0;
        d       <= '0;
        secondD <= 'h2;
        thirdD  <= 'h3;
        ack     <= 1'b0;
    end else begin
        if (b2C.req) begin
            d         <= b2C.data[$size(dSt)-1:0];
            secondD.d <= d;
            thirdD    <= secondD;
            ack       <= 1'b1;
            cState    <= 'h1; // cState change just to use it
        end else begin
            ack       <= 1'b0;
            cState    <= 'h0;
        end
    end
end

endmodule: blockCX