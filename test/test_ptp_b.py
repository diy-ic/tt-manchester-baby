# SPDX-FileCopyrightText: © 2024 Kristaps Jurkans
# SPDX-License-Identifier: MIT

import cocotb, random
from cocotb.triggers import Timer

@cocotb.test()
async def test_ptp_b(dut):

    # initial set up
    dut.reset_i.value = 1
    dut.control_i.value = 0
    dut.value_a_i.value = 0
    dut.value_b_i.value = 0

    await Timer(1, "ns")
    dut.reset_i.value = 0 
    
    # check if reset is successful
    assert dut.value_o.value == 0
    assert dut.uut_ptp_b.pointer_q.value == 0

    magic_value_a = 0xBAADF00D
    magic_value_b = 0xDEADBEEF
    combined_magic_value = (magic_value_a << 32) + magic_value_b

    dut.value_a_i.value = magic_value_a
    dut.value_b_i.value = magic_value_b

    await Timer(1, "ns")

    assert dut.uut_ptp_b.internal_concat.value == combined_magic_value

    # test full transmision
    for i in range(0, 8):
        expected = hex(combined_magic_value)[2:][0+(i*2) : 2+(i*2)]
        dut._log.info(f"expected: {expected}")

        dut.control_i.value = 1
        await Timer(1, "ns")
        dut._log.info(f"got: {hex(dut.value_o.value)[2:]}")
        assert dut.value_o.value == int(expected, 16)

        dut.control_i.value = 0
        await Timer(1, "ns")


    # test reset mid transmission
    for i in range(0, 4):
        dut.control_i.value = 1
        await Timer(1, "ns")
        dut.control_i.value = 0
        await Timer(1, "ns")
        if i == 2:
            dut.reset_i.value = 1
            await Timer(1, "ns")
            dut.reset_i.value = 0
            await Timer(1, "ns")
            assert dut.value_o.value == 0
            assert dut.uut_ptp_b.pointer_q.value == 0