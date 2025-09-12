# SPDX-FileCopyrightText: © 2024 Kristaps Jurkans
# SPDX-License-Identifier: MIT

import cocotb
from cocotb.triggers import Timer


READ = 0
WRITE = 1

class ManchesterBaby():

    def __init__(self, dut):

        self.program = [
            0x00000013, 0x0000401f, 0x0000601f, 0x0000401f,
            0x0000801e, 0x0000c000, 0x00000000, 0x0000401f,
            0x0000601f, 0x0000401c, 0x0000801c, 0x0000601c,
            0x0000401f, 0x0000801f, 0x0000601f, 0x0000401c,
            0x0000601c, 0x0000c000, 0x0000001a, 0x0000e000,
            0x0000601f, 0x0000401d, 0x0000801c, 0x0000801c,
            0x0000601c, 0x0000001b, 0x00000002, 0x0000000b,
            0x00000000, 0x20000000, 0x00000014, 0x00000024
        ]

        self.ptp_a_ctrl = dut.uio_in[0]
        self.ptp_b_ctrl = dut.uio_in[1]
        self.ptp_reset_n = dut.uio_in[2]
        self.debug_ptp = dut.uio_in[3]
        self.serialise = dut.uio_in[4]
        self.baby_reset_n = dut.rst_n

        self.baby_stop_lamp = dut.uio_out[6]
        self.baby_ram_rw = dut.uio_out[7]

        self.ptp_reset_n.value = 0
        self.ptp_a_ctrl.value = 0
        self.ptp_b_ctrl.value = 0
        self.debug_ptp.value = 0
        self.baby_reset_n.value = 0
        dut.ui_in.value = 0
        self.serialise.value = 0

        # unused signals
        dut.uio_in[7].value = 0
        dut.uio_in[6].value = 0
        dut.uio_in[5].value = 0

    async def _pulse_control_line(self) -> None:
        self.ptp_b_ctrl.value = 1
        await Timer(1, "us")
        self.ptp_b_ctrl.value = 0
        await Timer(1, "us")
    
    async def _read_32b(self, dut, serialise: bool = False) -> int:
        rx_value = 0
        if serialise:
            for i in range(32):
                await self._pulse_control_line()
                rx_value = rx_value << 1
                rx_value += dut.uo_out[0].value
        else:
            for i in range(4):
                await self._pulse_control_line()
                rx_value += dut.uo_out.value << 8 * (3-i)

        return rx_value


    async def get_ptp_b_data(self, dut, serialise: bool = False) -> list[int]:
        packet = [await self._read_32b(dut, serialise) for i in range(5)]
        return packet

    async def send_32b_ptp_a(self, dut, value: int, serialise: bool = False) -> None:
    
        if serialise:
            for i in range(32):
                digit = (value & (0x80000000 >> i)) >> 31-i

                dut.ui_in[0].value = digit

                await Timer(1, "us")
                self.ptp_a_ctrl.value = 1
                await Timer(1, "us")
                self.ptp_a_ctrl.value = 0
                await Timer(1, "us")
        else:
            byte_list = value.to_bytes(4)

            for byte in byte_list:
                dut.ui_in.value = byte

                await Timer(1, "us")
                self.ptp_a_ctrl.value = 1
                await Timer(1, "us")
                self.ptp_a_ctrl.value = 0
                await Timer(1, "us")

async def pulse_clock(dut, pulses=1):
    
    for i in range(pulses):
        dut.clk.value = 1
        await Timer(1, "us")
        dut.clk.value = 0
        await Timer(1, "us")

@cocotb.test()
async def test_ptp_wide(dut):
    dut.ena.value = 1
    dut.clk.value = 0
    baby = ManchesterBaby(dut)
    baby.baby_reset_n.value = 0 # keep baby off during testing
    await Timer(1, "us")

    # configure ptp_b
    baby.ptp_reset_n.value = 1
    baby.debug_ptp.value = 1
    baby.serialise.value = 0
    await Timer(1, "us")

    # debug_ptp forces magic values in pos 1 & 2
    data_1, data_2, _, _, _ = await baby.get_ptp_b_data(dut, serialise=False)

    assert data_1 == 0xDEADBEEF, "did not get expected magic value"
    assert data_2 == 0xCAFEB0BA, "did not get expected magic value"

    # reset
    baby.ptp_reset_n.value = 0
    await Timer(1, "us")
    baby.ptp_reset_n.value = 1
    await Timer(1, "us")

    magic_value = 0xBAADF00D
    await baby.send_32b_ptp_a(dut, magic_value, serialise=False)

    # present data - need ptp_a counter to hit 5
    baby.ptp_a_ctrl.value = 1
    await Timer(1, "us")
    baby.ptp_a_ctrl.value = 0
    await Timer(1, "us")

    _, _, data_1, _, _ = await baby.get_ptp_b_data(dut, serialise=False)
    assert data_1 == magic_value, f"data sent didn't match magic value - {hex(data_1)} != {hex(magic_value)}"


@cocotb.test()
async def test_ptp_narrow(dut):
    dut.ena.value = 1
    dut.clk.value = 0
    baby = ManchesterBaby(dut)
    baby.baby_reset_n.value = 0
    await Timer(1, "us")

    baby.ptp_reset_n.value = 1
    baby.serialise.value = 1
    baby.debug_ptp.value = 1
    await Timer(1, "us")

    data_1, data_2, _, _, _ = await baby.get_ptp_b_data(dut, serialise=True)
    assert data_1 == 0xDEADBEEF, "did not get expected magic value"
    assert data_2 == 0xCAFEB0BA, "did not get expected magic value"

    # reset
    baby.ptp_reset_n.value = 0
    await Timer(1, "us")
    baby.ptp_reset_n.value = 1
    await Timer(1, "us")

    magic_value = 0xBAADF00D
    await baby.send_32b_ptp_a(dut, magic_value, serialise=True)

    # present data - need ptp_a counter to hit 5
    baby.ptp_a_ctrl.value = 1
    await Timer(1, "us")
    baby.ptp_a_ctrl.value = 0
    await Timer(1, "us")

    _, _, data_1, _, _ = await baby.get_ptp_b_data(dut, serialise=True)
    assert data_1 == magic_value, f"data sent didn't match magic value - {hex(data_1)} != {hex(magic_value)}"        


@cocotb.test()
async def run_test_prog(dut):

    tick = 0
    def update_tick_counter(current_tick):
        return (current_tick + 1) % 8

    dut.ena.value = 1

    baby = ManchesterBaby(dut)

    await pulse_clock(dut, 2)

    baby.ptp_reset_n.value = 1
    baby.baby_reset_n.value = 1
    
    # initial state
    address = 0
    data_tx = baby.program[address]

    while True:

        await baby.send_32b_ptp_a(dut, data_tx)
        await pulse_clock(dut)
        tick = update_tick_counter(tick)
        await Timer(1, "us")

        rw_intent = baby.baby_ram_rw.value

        if baby.baby_stop_lamp == 1:
            break

        # present data - need ptp_a counter to hit 5
        baby.ptp_a_ctrl.value = 1
        await Timer(1, "us")
        baby.ptp_a_ctrl.value = 0
        await Timer(1, "us")
        

        address, data_rx, pc, ir, acc = await baby.get_ptp_b_data(dut)
        if tick == 0:
            dut._log.info(f"PC: {hex(pc)}, IR: {hex(ir)}, ACC: {hex(acc)}")

        if rw_intent == READ:
            data_tx = baby.program[address]
        elif rw_intent == WRITE:
            baby.program[address] = data_rx

    assert baby.baby_stop_lamp.value == 1, "stop lamp was not high, but still stopped responding?"
    assert baby.program[-4] == 0xe0000000, f"baby stopped but answer was not as expected (got {hex(baby.program[-4])} instead)"
