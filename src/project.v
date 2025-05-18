/*
 * Copyright (c) 2024 Kristaps Jurkans
 * SPDX-License-Identifier: Apache-2.0
*/

`default_nettype none

module tt_um_krisjdev_manchester_baby (
`ifdef QUARTUS_EXPOSE_FPGA_CLK_FOR_SIGNALTAP
    input wire fpga_clk,
`endif

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
      5 : input  : unused                 0
      4 : input  : serialise              0
      3 : input  : force debug values     0
      2 : input  : ptp reset_n            0
      1 : input  : ptp_b control          0
      0 : input  : ptp_a control          0
      mask:                           0b11000000
  */

  wire [31:0] w_ram_data_to_baby, w_ram_data_from_baby, w_state_ir, w_state_acc;
  wire [4:0] w_ram_addr, w_state_pc;

  // 8-bit value in from pico, 32-bit value to baby
  ptp_a ptp_a (
    .control_i(uio_in[0]), .reset_i(~uio_in[2]), .serialise_i(uio_in[4]),
    .value_i(ui_in), .value_o(w_ram_data_to_baby)
  );


  wire [31:0] ptp_in_a, ptp_in_b, ptp_in_c;

  // TODO: we might only just need 1 magic value?
  assign ptp_in_a = uio_in[3] ? 32'hDEADBEEF : w_ram_addr;
  assign ptp_in_b = uio_in[3] ? 32'hCAFEB0BA : w_ram_data_from_baby;
  assign ptp_in_c = uio_in[3] ? w_ram_data_to_baby : w_state_pc;

  // 2x 32-bit values from baby out to pico
  ptp_b ptp_b (
    .control_i(uio_in[1]), .reset_i(~uio_in[2]), .serialise_i(uio_in[4]),
    .value_a_i(ptp_in_a), .value_b_i(ptp_in_b), .value_c_i(ptp_in_c), 
    .value_d_i(w_state_ir), .value_e_i(w_state_acc),
    .value_o(uo_out)
  );

  main manchester_baby (
    .clock_i(clk), .reset_i(~rst_n), 
    .ram_data_i(w_ram_data_to_baby), .ram_data_o(w_ram_data_from_baby), 
    .ram_addr_o(w_ram_addr), .ram_rw_en_o(uio_out[7]), 
    .stop_lamp_o(uio_out[6]),
    .state_ir_o(w_state_ir), .state_acc_o(w_state_acc), .state_pc_o(w_state_pc)
  );

  assign uio_oe = 8'b11000000;
  assign uio_out[5:0] = 6'h0;

endmodule
