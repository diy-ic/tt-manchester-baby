// parallel to parallel type A
// use on manchester baby ram data input side
module ptp_a (
    input control_i,
    input reset_i,
    input [7:0] value_i,
    output reg [31:0] value_o
);

    always @ (posedge control_i or posedge reset_i) begin
        
        if (reset_i) begin
            value_o <= 32'b0;
        end else begin
            value_o <= {value_o[23:0], value_i};
        end

    end

endmodule