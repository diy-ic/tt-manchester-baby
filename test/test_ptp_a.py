# SPDX-FileCopyrightText: © 2024 Kristaps Jurkans
# SPDX-License-Identifier: MIT

import cocotb, random
from cocotb.triggers import Timer

@cocotb.test()
async def test_ptp_a(dut):

    # initial set up
    dut.reset_i.value = 1
    dut.value_i.value = 0
    dut.control_i.value = 0

    await Timer(1, "ns")
    dut.reset_i.value = 0 
    
    # check if reset is successful
    assert dut.value_o.value == 0
    
    transmitted_value = 0
    for i in range(0, 4):
        rand_value = random.randrange(0, 256)

        dut._log.info(f"random value: {hex(rand_value)}")
        dut.value_i.value = rand_value
        
        transmitted_value += rand_value
        if i != 3:
            transmitted_value = transmitted_value << 8

        dut._log.info(f"transmitted value: {hex(transmitted_value)}")

        dut.control_i.value = 1
        await Timer(1, "ns")

        dut.control_i.value = 0
        await Timer(1, "ns")

    assert hex(dut.value_o.value) == hex(transmitted_value)