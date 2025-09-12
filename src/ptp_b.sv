// parallel to parallel type B
// use on manchester baby outputs (ram/addr)
module ptp_b (
    input reset_i, control_i, serialise_i, debug_i,
    input [31:0] value_a_i, value_b_i, value_c_i, value_d_i, value_e_i, value_f_i,
    output logic [7:0] value_o
);

    // 32bit x 5 signals = 160
    localparam CONCAT_SIGNAL_WIDTH = 160;

    logic [7:0] pointer_q;
    logic [CONCAT_SIGNAL_WIDTH-1:0] internal_concat;
    
    // this is a little messy
    // the signals change depending on whether the debug signal is asserted
    // if asserted, it will output some magic values & mirror the input from ptp_a
    // otherwise, it will output the signals as normal
    assign internal_concat = debug_i ? {32'hDEADBEEF, 32'hCAFEB0BA, value_f_i, 32'h0, 32'h0} :
                                       {value_a_i, value_b_i, value_c_i, value_d_i, value_e_i};

    always @ (posedge control_i or posedge reset_i) begin
        
        if (reset_i) begin
            value_o <= 'd0;
            pointer_q <= 'd0;
        end else begin

            if (serialise_i) begin
                pointer_q <= pointer_q >= CONCAT_SIGNAL_WIDTH-1 ? 'd0 : pointer_q + 'd1;
                value_o <= {7'b0, internal_concat[CONCAT_SIGNAL_WIDTH-1 - pointer_q]};
            end else begin
                // 19 = 160 (the total length of signals we have) / 8 bits
                pointer_q <= pointer_q >= 'd19 ? 'd0 : pointer_q + 'd1; 
                value_o <= internal_concat[(CONCAT_SIGNAL_WIDTH-1) -(pointer_q * 8) -: 8];
            end
        end
    end
endmodule