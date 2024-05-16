// parallel to parallel type A
// use on manchester baby ram data input side
module ptp_a (
    input control_i, reset_i,
    input [7:0] value_i,
    output reg [31:0] value_o
);

    reg [31:0] internal_shift_reg;
    reg [2:0] counter;

    always @ (posedge control_i or posedge reset_i) begin
        
        if (reset_i) begin
            value_o <= 32'b0;
            counter <= 3'b0;
            internal_shift_reg <= 32'b0;
        end else begin
            counter <= counter + 1;
            internal_shift_reg <= {internal_shift_reg[23:0], value_i};
            // value_o <= {value_o[23:0], value_i};

            if (counter == 3'b100) begin
                value_o <= internal_shift_reg;
                counter <= 3'b0;
            end
        end

    end

endmodule