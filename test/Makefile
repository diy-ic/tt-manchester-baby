# Makefile
# See https://docs.cocotb.org/en/stable/quickstart.html for more info

# defaults
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
SRC_DIR = $(PWD)/../src
LOGISIM_HDL_DIR = /openlane-manchester-baby/logisim/hdl
BABY_SRC_RTL_DIR = /openlane-manchester-baby/src

PROJECT_SOURCES = project.v

PROJECT_SOURCES += ptp_a.sv
PROJECT_SOURCES += ptp_b.sv
PROJECT_SOURCES += manchester_baby.v
PROJECT_SOURCES += $(LOGISIM_HDL_DIR)/base/logisimTickGenerator.v
PROJECT_SOURCES += $(LOGISIM_HDL_DIR)/base/LogisimClockComponent.v
PROJECT_SOURCES += $(LOGISIM_HDL_DIR)/gates/AND_GATE.v
PROJECT_SOURCES += $(LOGISIM_HDL_DIR)/gates/OR_GATE_BUS_5_INPUTS.v
PROJECT_SOURCES += $(LOGISIM_HDL_DIR)/gates/OR_GATE_3_INPUTS.v
PROJECT_SOURCES += $(LOGISIM_HDL_DIR)/gates/OR_GATE.v
PROJECT_SOURCES += $(LOGISIM_HDL_DIR)/gates/OR_GATE_BUS.v
PROJECT_SOURCES += $(LOGISIM_HDL_DIR)/circuit/main.v
PROJECT_SOURCES += $(LOGISIM_HDL_DIR)/toplevel/logisimTopLevelShell.v
PROJECT_SOURCES += $(LOGISIM_HDL_DIR)/plexers/Decoder_8.v
PROJECT_SOURCES += $(LOGISIM_HDL_DIR)/plexers/Multiplexer_bus_2.v
PROJECT_SOURCES += $(LOGISIM_HDL_DIR)/arith/Adder.v
PROJECT_SOURCES += $(LOGISIM_HDL_DIR)/arith/Comparator.v
PROJECT_SOURCES += $(LOGISIM_HDL_DIR)/arith/Subtractor.v
PROJECT_SOURCES += $(LOGISIM_HDL_DIR)/memory/REGISTER_FLIP_FLOP.v
PROJECT_SOURCES += $(LOGISIM_HDL_DIR)/memory/LogisimCounter.v
PROJECT_SOURCES += $(LOGISIM_HDL_DIR)/memory/S_R_FLIPFLOP.v
# PROJECT_SOURCES += $(BABY_SRC_RTL_DIR)/manchester_baby.v

ifneq ($(GATES),yes)

# RTL simulation:
SIM_BUILD				= sim_build/rtl
VERILOG_SOURCES += $(addprefix $(SRC_DIR)/,$(PROJECT_SOURCES))
COMPILE_ARGS 		+= -I$(SRC_DIR)

else

# Gate level simulation:
SIM_BUILD				= sim_build/gl
COMPILE_ARGS    += -DGL_TEST
COMPILE_ARGS    += -DFUNCTIONAL
COMPILE_ARGS    += -DUSE_POWER_PINS
COMPILE_ARGS    += -DSIM
COMPILE_ARGS    += -DUNIT_DELAY=\#1
VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/primitives.v
VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v

# this gets copied in by the GDS action workflow
VERILOG_SOURCES += $(PWD)/gate_level_netlist.v

endif

# Include the testbench sources:
VERILOG_SOURCES += $(PWD)/tb.v 
TOPLEVEL = tb

# MODULE is the basename of the Python test file
MODULE = test

# test_ptp_a:
	# $(MAKE) sim MODULE=test_ptp_a TOPLEVEL=tb_ptp_a

# test_ptp_b:
	# $(MAKE) sim MODULE=test_ptp_b TOPLEVEL=tb_ptp_b

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim
