# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: MIT

import cocotb
from cocotb.triggers import Timer, Edge, RisingEdge, First, Combine, ClockCycles, FallingEdge
from cocotb.clock import Clock
from cocotb.types import Logic, LogicArray, Range
from cocotb.handle import Release


@cocotb.test()
async def run_test_prog(dut):

    program = [
        0x00000013, 0x0000401f, 0x0000601f, 0x0000401f,
        0x0000801e, 0x0000c000, 0x00000000, 0x0000401f,
        0x0000601f, 0x0000401c, 0x0000801c, 0x0000601c,
        0x0000401f, 0x0000801f, 0x0000601f, 0x0000401c,
        0x0000601c, 0x0000c000, 0x0000001a, 0x0000e000,
        0x0000601f, 0x0000401d, 0x0000801c, 0x0000801c,
        0x0000601c, 0x0000001b, 0x00000002, 0x0000000b,
        0x00000000, 0x20000000, 0x00000014, 0x00000024
    ]

    cocotb.start_soon(Clock(dut.clk, 1, units="ns").start())

    dut.ena.value = 1

    ptp_a_ctrl = dut.uio_in[0]
    ptp_b_ctrl = dut.uio_in[1]
    ptp_reset_n = dut.uio_in[2]
    baby_reset_n = dut.uio_in[3]
    baby_allow_exec = dut.uio_in[4]

    baby_clock_io_out = dut.uio_out[5]
    baby_clock = dut.user_project.w_baby_internal_clock
    baby_stop_lamp = dut.uio_out[6]
    baby_ram_rw = dut.uio_out[7] # 0 = read, 1 = write

    ptp_reset_n.value = 0
    ptp_a_ctrl.value = 0
    ptp_b_ctrl.value = 0
    baby_reset_n.value = 0
    dut.rst_n.value = 0
    baby_allow_exec.value = 0
    dut.ui_in.value = 0
    await ClockCycles(dut.clk, 10)


    baby_allow_exec.value = 1
    await ClockCycles(dut.clk, 1)
    ptp_reset_n.value = 1
    baby_reset_n.value = 1
    await ClockCycles(dut.clk, 1)
    
    async def _stop_baby_exec():
        baby_allow_exec.value = 0
        await RisingEdge(dut.clk)

    async def _start_baby_exec():
        baby_allow_exec.value = 1
        await RisingEdge(dut.clk)


    # initial state
    address = 0
    data_tx = program[address]

    while True:

        # ready data for rising clock edge
        await _stop_baby_exec()
        await send_32b_ptp_a(dut, data_tx)
        await _start_baby_exec()

        await RisingEdge(baby_clock)

        # wait for signal to propagate just in case baby wants to write
        await RisingEdge(dut.clk)
        rw_intent = baby_ram_rw.value

        if baby_stop_lamp.value == 1:
            break

        # present data -- this will increment the counter and update the reg
        ptp_a_ctrl.value = 1
        await RisingEdge(dut.clk)
        ptp_a_ctrl.value = 0
        await RisingEdge(dut.clk)


        await _stop_baby_exec()
        address, data_rx = await get_ptp_b_data(dut)
        
        if rw_intent == 0: # read
            data_tx = program[address]
        elif rw_intent == 1: # write
            program[address] = data_rx

        await _start_baby_exec()


    assert baby_stop_lamp.value == 1, "stop lamp was not high, but still stopped responding?"
    assert program[-4] == 0xe0000000, "baby stopped but answer was not as expected"



async def get_ptp_b_data(dut):
    ptp_b_ctrl = dut.uio_in[1]

    address = 0
    data = 0

    async def _pulse_control_line():
        ptp_b_ctrl.value = 1
        await Timer(1, "ns")
        ptp_b_ctrl.value = 0
        await Timer(1, "ns")
    
    for i in range(4):
        await _pulse_control_line()
        address += dut.uo_out.value
        if i != 3:
            address = address << 8


    for i in range(4):
        await _pulse_control_line()
        data += dut.uo_out.value
        if i != 3:
            data = data << 8

    dut._log.info(f"[ptp_b] got: address = {hex(address)}, data = {hex(data)}")

    return address, data

async def send_32b_ptp_a(dut, value_to_send:int):
    ptp_a_ctrl = dut.uio_in[0]
    
    byte_list = value_to_send.to_bytes(4)
    dut._log.info(f"[ptp_a] sending: {hex(value_to_send)}")

    for byte in byte_list:
        
        dut.ui_in.value = byte
 
        await Timer(1, "ns")
        ptp_a_ctrl.value = 1
        await Timer(1, "ns")
        ptp_a_ctrl.value = 0
        await Timer(1, "ns")
