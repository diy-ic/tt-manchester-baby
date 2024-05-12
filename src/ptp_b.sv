// parallel to parallel type B
// use on manchester baby outputs (ram/addr)
module ptp_b (
    input reset_i, control_i,
    input [31:0] value_a_i, value_b_i,
    output reg [7:0] value_o
);

    reg [2:0] pointer_q;
    wire [63:0] internal_concat;
    
    assign internal_concat = {value_a_i, value_b_i};

    always @ (posedge control_i or posedge reset_i) begin
        
        if (reset_i) begin
            value_o <= 0;
            pointer_q <= 0;
        end else begin
            pointer_q <= pointer_q + 1;
            value_o <= internal_concat[63 -(pointer_q * 8) -: 8];
        end
        
    end 

endmodule