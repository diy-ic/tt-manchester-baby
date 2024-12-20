// parallel to parallel type B
// use on manchester baby outputs (ram/addr)
module ptp_b (
    input reset_i, control_i,
    input [31:0] value_a_i, value_b_i, value_c_i, value_d_i, value_e_i,
    output reg [7:0] value_o
);

    // 32bit x 5 signals = 160
    localparam CONCAT_SIGNAL_WIDTH = 160;

    reg [4:0] pointer_q;
    wire [CONCAT_SIGNAL_WIDTH-1:0] internal_concat;
    // wire [63:0] internal_concat;
    
    // im sure there's a nicer way with loops or arrays but this will do
    assign internal_concat = {value_a_i, value_b_i, value_c_i, value_d_i, value_e_i};
    // assign internal_concat = {value_a_i, value_b_i};

    always @ (posedge control_i or posedge reset_i) begin
        
        if (reset_i) begin
            value_o <= 0;
            pointer_q <= 0;
        end else begin
            pointer_q <= pointer_q >= 19 ? 0 : pointer_q + 1; 
            value_o <= internal_concat[(CONCAT_SIGNAL_WIDTH-1) -(pointer_q * 8) -: 8];
        end
        
    end 

endmodule