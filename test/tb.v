`default_nettype none
`timescale 1ns / 1ps

/* This testbench just instantiates the module and makes some convenient wires
   that can be driven / tested by the cocotb test.py.
*/
module tb ();

`ifdef COCOTB_SIM
  initial begin
    $dumpfile("tb.vcd");
    $dumpvars(0, tb);
    #1;
  end
`endif


  reg clock;
  reg reset_i;
  reg [31:0] ram_data_i;
  wire [31:0] ram_data_o;
  wire [4:0] ram_addr_o;
  wire ram_rw_en_o; // 0 = read, 1 = write
  wire stop_lamp_o;
  wire clock_o; 


  manchester_baby uut_mb (
    .clock(clock), .reset_i(reset_i), .ram_data_i(ram_data_i), .ram_data_o(ram_data_o),
    .ram_addr_o(ram_addr_o), .ram_rw_en_o(ram_rw_en_o), .stop_lamp_o(stop_lamp_o), .clock_o(clock_o)
  );




// use later vvvvvvvvvv


  // Wire up the inputs and outputs:
  // reg clk;
  // reg rst_n;
  // reg ena;
  // reg [7:0] ui_in;
  // reg [7:0] uio_in;
  // wire [7:0] uo_out;
  // wire [7:0] uio_out;
  // wire [7:0] uio_oe;

  // Replace tt_um_example with your module name:
  // tt_um_example user_project (

      // Include power ports for the Gate Level test:
// `ifdef GL_TEST
      // .VPWR(1'b1),
      // .VGND(1'b0),
// `endif

      // .ui_in  (ui_in),    // Dedicated inputs
      // .uo_out (uo_out),   // Dedicated outputs
      // .uio_in (uio_in),   // IOs: Input path
      // .uio_out(uio_out),  // IOs: Output path
      // .uio_oe (uio_oe),   // IOs: Enable path (active high: 0=input, 1=output)
      // .ena    (ena),      // enable - goes high when design is selected
      // .clk    (clk),      // clock
      // .rst_n  (rst_n)     // not reset
  // );

endmodule


module tb_ptp_a ();

`ifdef COCOTB_SIM
  initial begin
    $dumpfile("tb_ptp_a.vcd");
    $dumpvars(0, tb_ptp_a);
    #1;
  end
`endif

  reg control_i;
  reg reset_i;
  reg [7:0] value_i;
  wire [31:0] value_o;

  ptp_a uut_ptp_a (
    .control_i(control_i), .reset_i(reset_i), .value_i(value_i), .value_o(value_o)
  );

endmodule
