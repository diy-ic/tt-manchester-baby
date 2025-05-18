// parallel to parallel type A
// use on manchester baby ram data input side
module ptp_a (
    input control_i, reset_i, serialise_i,
    input [7:0] value_i,
    output logic [31:0] value_o
);

    logic [31:0] internal_shift_reg;
    logic [5:0] counter;

    always @ (posedge control_i or posedge reset_i) begin
        
        if (reset_i) begin
            value_o <= 32'b0;
            counter <= 'b0;
            internal_shift_reg <= 32'b0;
        end else begin
            counter <= counter + 1;

            // change shift register data input depending on serialise_i signal
            if (serialise_i) begin
                internal_shift_reg <= {internal_shift_reg[30:0], value_i[0]};
            end else begin
                internal_shift_reg <= {internal_shift_reg[23:0], value_i};
            end

            if (serialise_i) begin
                if (counter == 'd32) begin
                    value_o <= internal_shift_reg;
                    counter <= 'd0;
                end
            end else begin
                if (counter == 'b100) begin
                    value_o <= internal_shift_reg;
                    counter <= 'b0;
                end
            end
        end

    end

endmodule