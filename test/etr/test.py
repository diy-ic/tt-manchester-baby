import microcotb as cocotb
from microcotb.triggers import Timer

from ttboard.demoboard import DemoBoard, RPMode
from ttboard.cocotb.dut import DUT

cocotb.set_runner_scope(__name__)

class ManchesterBaby(DUT):
    def __init__(self):
        super().__init__("Manchester Baby")

        self.add_bit_attribute("ptp_a_ctrl", self.tt.uio_in, 0)
        self.add_bit_attribute("ptp_b_ctrl", self.tt.uio_in, 1)
        self.add_bit_attribute("ptp_reset_n", self.tt.uio_in, 2)
        self.add_bit_attribute("debug_ptp", self.tt.uio_in, 3)
        self.add_bit_attribute("serialise", self.tt.uio_in, 4)
        # NOTE: cannot assign custom name to reset pin
        # self.add_bit_attribute("baby_reset_n", self.tt.rst_n)

        self.add_bit_attribute("baby_stop_lamp", self.tt.uio_out, 6)
        self.add_bit_attribute("baby_ram_rw", self.tt.uio_out, 7)

        self.add_slice_attribute("data_in", self.tt.ui_in, 7, 0)
        self.add_slice_attribute("data_out", self.tt.uo_out, 7, 0)

        # must be the opposite of the ASIC project
        # ASIC[OUTPUT, EN=1] ----> DEMOBOARD[INPUT,  EN=0]
        # ASIC[INPUT,  EN=0] <---- DEMOBOARD[OUTPUT, EN=1]
        # so here we are expecting two signals to be received by the demoboard from the project (marked as 0)
        self.uio_oe_pico.value = 0b00111111

    async def _pulse_control_line(self) -> None:
        self.ptp_b_ctrl.value = 1
        await Timer(1, "us")
        self.ptp_b_ctrl.value = 0
        await Timer(1, "us")

    async def _read_32b(self) -> int:
        rx_value = 0

        if (self.serialise.value):
            for i in range(32):
                await self._pulse_control_line()
                rx_value = rx_value << 1
                # NOTE: cannot do self.data_out[0].value as it returns Logic
                rx_value += int(self.data_out[0])
        else:
            for i in range(4):
                await self._pulse_control_line()
                # NOTE: cannot perform shift operators on LogicArray
                # rx_value += self.data_out.value << 8 * (3-i)
                rx_value += int(self.data_out.value) << 8 * (3-i)

        return rx_value

    async def get_ptp_b_data(self) -> list[int]:
        packet = []
        for i in range(5):
            packet.append(await self._read_32b())
        # NOTE: cannot use await in list comprehension
        # packet = [await self._read_32b() for i in range(5)]

        return packet

    async def send_32b_ptp_a(self, value: int) -> None:

        if (self.serialise.value):
            for i in range(32):
                digit = (value & (0x80000000 >> i)) >> 31-i
                # NOTE: writing to self.data_in[0].value fails silently
                self.data_in[0] = digit

                await Timer(1, "us")
                self.ptp_a_ctrl.value = 1
                await Timer(1, "us")
                self.ptp_a_ctrl.value = 0
                await Timer(1, "us")
        else:
            byte_list = value.to_bytes(4)

            for byte in byte_list:
                self.data_in.value = byte

                await Timer(1, "us")
                self.ptp_a_ctrl.value = 1
                await Timer(1, "us")
                self.ptp_a_ctrl.value = 0
                await Timer(1, "us")


# test parallel output feature
@cocotb.test()
async def test_ptp_wide(dut: ManchesterBaby):
    dut.ena.value = 1
    dut.clk.value = 0

    # keep baby off during testing
    dut.rst_n.value = 0
    await Timer(1, "us")

    # configure ptp_wide
    dut.ptp_reset_n.value = 1
    dut.debug_ptp.value = 1
    dut.serialise.value = 0

    # debug forces magic values into pos 1 & 2
    data_1, data_2, _, _, _ = await dut.get_ptp_b_data()

    assert data_1 == 0xDEADBEEF, f"expected 0xDEADBEEF, got {hex(data_1)}"
    assert data_2 == 0xCAFEB0BA, f"expected 0xCAFEB0BA, got {hex(data_2)}"

    # reset
    dut.ptp_reset_n.value = 0
    await Timer(1, "us")
    dut.ptp_reset_n.value = 1
    await Timer(1, "us")

    magic_value = 0xBAADF00D
    await dut.send_32b_ptp_a(magic_value)

    # present data - need ptp_a counter to hit 5
    dut.ptp_a_ctrl.value = 1
    await Timer(1, "us")
    dut.ptp_a_ctrl.value = 0
    await Timer(1, "us")

    _, _, data_3, _, _ = await dut.get_ptp_b_data()
    assert data_3 == magic_value, f"data sent didn't match magic value - {hex(data_3)} != {hex(magic_value)}"

# test serial output feature
@cocotb.test()
async def test_ptp_narrow(dut: ManchesterBaby):
    dut.ena.value = 1
    dut.clk.value = 0

    # keep baby off during testing
    dut.rst_n.value = 0
    await Timer(1, "us")

    dut.ptp_reset_n.value = 1
    dut.serialise.value = 1
    dut.debug_ptp.value = 1
    await Timer(1, "us")

    data_1, data_2, _, _, _ = await dut.get_ptp_b_data()

    assert data_1 == 0xDEADBEEF, f"expected 0xDEADBEEF, got {hex(data_1)}"
    assert data_2 == 0xCAFEB0BA, f"expected 0xCAFEB0BA, got {hex(data_2)}"

    # reset
    dut.ptp_reset_n.value = 0
    await Timer(1, "us")
    dut.ptp_reset_n.value = 1
    await Timer(1, "us")

    magic_value = 0xBAADF00D
    await dut.send_32b_ptp_a(magic_value)

    # present data - need ptp_a counter to hit 5
    dut.ptp_a_ctrl.value = 1
    await Timer(1, "us")
    dut.ptp_a_ctrl.value = 0
    await Timer(1, "us")

    _, _, data_3, _, _ = await dut.get_ptp_b_data()
    assert data_3 == magic_value, f"data sent didn't match magic value - {hex(data_3)} != {hex(magic_value)}"

def main():
    tt = DemoBoard.get()

    if not tt.shuttle.has("tt_um_krisjdev_manchester_baby"):
        print("shuttle doesn't contain manchester baby project")
        return False

    tt.shuttle.tt_um_krisjdev_manchester_baby.enable()

    # control I/O
    if tt.mode != RPMode.ASIC_RP_CONTROL:
        print("setting mode to ASIC_RP_CONTROL")
        tt.mode = RPMode.ASIC_RP_CONTROL

    dut = ManchesterBaby()
    dut._log.info("enabled project, beginning tests")

    runner = cocotb.get_runner()
    runner.test(dut)

if __name__ == "__main__":
    main()