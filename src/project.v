/*
 * Copyright (c) 2024 Kristaps Jurkans
 * SPDX-License-Identifier: Apache-2.0
*/

`default_nettype none

module tt_um_krisjdev_manchester_baby (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  /*
    io mapping

    inputs:
      7:0 : parallel data input to ptp_a -- baby input
    
    outputs:
      7:0 : parallel data output from ptp_b -- baby output

    bidir:
      7 : output : ram_rw_en_o            1
      6 : output : stop_lamp_o            1
      5 : output : clock_o                1
      4 : input  : allow baby exec        0
      3 : input  : baby reset_n           0
      2 : input  : ptp reset_n            0
      1 : input  : ptp_b control          0
      0 : input  : ptp_a control          0
      mask:                           0b11100000
  */

  wire [31:0] w_ram_data_to_baby, w_ram_data_from_baby;
  wire [4:0] w_ram_addr;

  // 8-bit value in from pico, 32-bit value to baby
  ptp_a ptp_a (
    .control_i(uio_in[0]), .reset_i(~uio_in[2]), .value_i(ui_in), .value_o(w_ram_data_to_baby)
  );

  // 2x 32-bit values from baby out to pico
  ptp_b ptp_b (
    .control_i(uio_in[1]), .reset_i(~uio_in[2]), .value_a_i({27'h0, w_ram_addr}), .value_b_i(w_ram_data_from_baby),
    .value_o(uo_out)
  );

  manchester_baby manchester_baby (
    .clock(clk), 
    .reset_i(~uio_in[3]), .ram_data_i(w_ram_data_to_baby), 
    .ram_data_o(w_ram_data_from_baby), .ram_addr_o(w_ram_addr), .ram_rw_en_o(uio_out[7]), 
    .stop_lamp_o(uio_out[6])
  );

  assign uio_oe = 8'b11100000;
  assign uio_out[5:0] = 'h0;

endmodule
