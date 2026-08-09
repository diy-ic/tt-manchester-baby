from time import sleep_us

import ttboard.util.platform as plat

from ttboard.demoboard import DemoBoard


class ManchesterBaby():
    def __init__(self):
        tt = DemoBoard.get()
        self.tt = tt
        tt.uio_oe_pico.value = 0b00111111

    # getters/setters for each pin
    # TODO: better way to do this?
    @property
    def ptp_a_ctrl(self):
        return self.tt.uio_in[0]

    @ptp_a_ctrl.setter
    def ptp_a_ctrl(self, value):
        self.tt.uio_in[0] = value

    @property
    def ptp_b_ctrl(self):
        return self.tt.uio_in[1]

    @ptp_b_ctrl.setter
    def ptp_b_ctrl(self, value):
        self.tt.uio_in[1] = value

    @property
    def ptp_reset_n(self):
        return self.tt.uio_in[2]

    @ptp_reset_n.setter
    def ptp_reset_n(self, value):
        self.tt.uio_in[2] = value

    @property
    def debug_ptp(self):
        return self.tt.uio_in[3]

    @debug_ptp.setter
    def debug_ptp(self, value):
        self.tt.uio_in[3] = value

    @property
    def serialise(self):
        return self.tt.uio_in[4]

    @serialise.setter
    def serialise(self, value):
        self.tt.uio_in[4] = value

    @property
    def baby_stop_lamp(self):
        return self.tt.uio_out[6]

    @property
    def baby_ram_rw(self):
        return self.tt.uio_out[7]

    @property
    def data_in(self):
        return self.tt.ui_in

    @data_in.setter
    def data_in(self, value):
        self.tt.ui_in = value

    @property
    def data_out(self):
        return self.tt.uo_out

    @property
    def rst_n(self):
        return self.tt.rst_n()

    @rst_n.setter
    def rst_n(self, value):
        if value == 1:
            self.tt.reset_project(False)
        elif value == 0:
            self.tt.reset_project(True)
        else:
            raise ValueError("must be 1 or 0")

    def _pulse_control_line(self) -> None:
        self.ptp_b_ctrl = 1
        self.ptp_b_ctrl = 0

    def _pulse_clock(self, pulses=1) -> None:
        for i in range(pulses):
            # HACK: need to combine tt.clk() with plat.write_clock() for clock to work
            self.tt.clk(1)
            plat.write_clock(1)
            plat.write_clock(0)
            self.tt.clk(0)

    def _read_32b(self) -> int:
        rx_value = 0

        if (self.serialise):
            for i in range(32):
                self._pulse_control_line()
                rx_value = rx_value << 1
                # NOTE: cannot do self.data_out[0].value as it returns Logic
                rx_value += int(self.data_out[0])
        else:
            for i in range(4):
                self._pulse_control_line()
                # NOTE: cannot perform shift operators on LogicArray
                # rx_value += self.data_out.value << 8 * (3-i)
                rx_value += int(self.data_out) << 8 * (3-i)

        return rx_value

    def get_ptp_b_data(self) -> list[int]:
        packet = []
        for i in range(5):
            packet.append(self._read_32b())
        # NOTE: cannot use await in list comprehension
        # packet = [await self._read_32b() for i in range(5)]

        return packet

    def send_32b_ptp_a(self, value: int) -> None:
        if (self.serialise):
            for i in range(32):
                digit = (value & (0x80000000 >> i)) >> 31-i
                # NOTE: writing to self.data_in[0].value fails silently
                self.data_in[0] = digit

                self.ptp_a_ctrl = 1
                self.ptp_a_ctrl = 0
        else:
            byte_list = value.to_bytes(4)

            for byte in byte_list:
                self.data_in = byte

                self.ptp_a_ctrl = 1
                self.ptp_a_ctrl = 0

    def execute(self, program: list[int]):
        READ = 0
        WRITE = 1

        tick = 0
        def update_tick(current_tick):
            return (current_tick + 1) % 8

        self.ptp_reset_n = 0
        self.ptp_a_ctrl = 0
        self.ptp_b_ctrl = 0
        self.debug_ptp = 0
        self.rst_n = 0
        self.data_in = 0
        self.serialise = 0

        self._pulse_clock(2)

        self.ptp_reset_n = 1
        self.rst_n = 1

        address = 0
        data_tx = program[address]

        while True:
            self.send_32b_ptp_a(data_tx)
            self._pulse_clock(1)

            tick = update_tick(tick)

            rw_intent = self.baby_ram_rw

            if self.baby_stop_lamp == 1:
                break

            self.ptp_a_ctrl = 1
            self.ptp_a_ctrl = 0

            address, data_rx, pc, ir, acc = self.get_ptp_b_data()

            if tick == 0:
                print(f"PC: {hex(pc)}, IR: {hex(ir)}, ACC: {hex(acc)}")

            if rw_intent == READ:
                data_tx = program[address]
            elif rw_intent == WRITE:
                program[address] = data_rx

        print(f"stop lamp: {self.baby_stop_lamp}")
        print(hex(program[-4]))