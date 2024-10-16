# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-FileCopyrightText: © 2024 Kristaps Jurkans
# SPDX-License-Identifier: MIT

import cocotb
from cocotb.triggers import Timer


READ = 0
WRITE = 1

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

async def pulse_clock(dut, pulses=1):
    
    for i in range(pulses):
        dut.clk.value = 1
        await Timer(1, "ns")
        dut.clk.value = 0
        await Timer(1, "ns")

@cocotb.test()
async def run_test_prog(dut):

    tick = 0
    def update_tick_counter(current_tick):
        return (current_tick + 1) % 8

    is_gate_level_test = False

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

    dut.ena.value = 1

    ptp_a_ctrl = dut.uio_in[0]
    ptp_b_ctrl = dut.uio_in[1]
    ptp_reset_n = dut.uio_in[2]
    baby_reset_n = dut.rst_n

    baby_stop_lamp = dut.uio_out[6]
    baby_ram_rw = dut.uio_out[7] # 0 = read, 1 = write

    ptp_reset_n.value = 0
    ptp_a_ctrl.value = 0
    ptp_b_ctrl.value = 0
    baby_reset_n.value = 0
    dut.rst_n.value = 0
    dut.ui_in.value = 0

    await pulse_clock(dut, 2)

    ptp_reset_n.value = 1
    baby_reset_n.value = 1
    
    # initial state
    address = 0
    data_tx = program[address]

    while True:

        await send_32b_ptp_a(dut, data_tx)
        await pulse_clock(dut)
        tick = update_tick_counter(tick)
        await Timer(1, "ns")

        rw_intent = baby_ram_rw.value

        if baby_stop_lamp == 1:
            break

        # present data - need ptp_a counter to hit 5
        ptp_a_ctrl.value = 1
        await Timer(1, "ns")
        ptp_a_ctrl.value = 0
        await Timer(1, "ns")
        

        address, data_rx = await get_ptp_b_data(dut)

        if rw_intent == READ:
            data_tx = program[address]
        elif rw_intent == WRITE:
            program[address] = data_rx

        # gate level test fails because we cant probe the hierarchy any more
        if not is_gate_level_test:
            try:
                dut._log.info(f"[machine] PC: {hex(dut.user_project.manchester_baby.manchester_baby_instance.CIRCUIT_0.PC.q.value)}, " \
                f"IR: {hex(dut.user_project.manchester_baby.manchester_baby_instance.CIRCUIT_0.IR.q.value)}, " \
                f"ACC: {hex(dut.user_project.manchester_baby.manchester_baby_instance.CIRCUIT_0.Acc.q.value)}, " \
                f"tick: {tick}")
            except AttributeError:
                is_gate_level_test = True

    assert baby_stop_lamp.value == 1, "stop lamp was not high, but still stopped responding?"
    assert program[-4] == 0xe0000000, f"baby stopped but answer was not as expected (got {hex(program[-4])} instead)"