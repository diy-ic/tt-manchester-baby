from time import sleep_us
from sys import stdin

import ttboard.util.platform as plat

from ttboard.demoboard import DemoBoard


GLYPHS = [
    "· · · ·", "■ · · ·", "· ■ · ·", "■ ■ · ·",     # 0000, 0001, 0010, 0011
    "· · ■ ·", "■ · ■ ·", "· ■ ■ ·", "■ ■ ■ ·",     # 0100, 0101, 0110, 0111
    "· · · ■", "■ · · ■", "· ■ · ■", "■ ■ · ■",     # 1000, 1001, 1010, 1011
    "· · ■ ■", "■ · ■ ■", "· ■ ■ ■", "■ ■ ■ ■",     # 1100, 1101, 1110, 1111
]

class ManchesterBaby():
    def __init__(self):
        tt = DemoBoard.get()
        self.tt = tt
        tt.uio_oe_pico.value = 0b00111111
        self.program = None

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

    def draw_crt(self):

        for i in range(len(self.program)):
            print(f"0x{i:0{2}x} | ", end="")

            # set colour to green
            print("\033[32m", end="")

            for j in range(8):
                glyph_index = (self.program[i] & (0xF << (j*4))) >> j * 4
                print(f"{GLYPHS[glyph_index]} ", end="")

            print("\033[0m", end="")
            print(f"| 0x{self.program[i]:0{8}x}")

        print("")
        print("PC   | ")
        print("IR   | ")
        print("ACC  | ")

    def get_cursor_position(self):
        print("\033[6n", end="")

        xpos_str = []
        ypos_str = []
        write_xpos = True
        pos_index = 0

        while True:
            read_byte = stdin.read(1)

            if read_byte == "\033" or read_byte == "[": continue
            if read_byte == "R": break

            if read_byte == ";":
                write_xpos = False
                pos_index = 0
                continue

            if write_xpos:
                xpos_str.append(read_byte)
            else:
                ypos_str.append(read_byte)

            pos_index += 1

        xpos = "".join(xpos_str)
        ypos = "".join(ypos_str)

        return [xpos, ypos]

    def update_crt_line(self, pos, value):
        cursor_xy = self.get_cursor_position()

        # move cursor to start of crt line for given address
        print(f"\033[{pos};8H", end="")
        print(f"\033[32m", end="")

        for i in range(8):
            glyph_index = (value & 0xF << (i*4)) >> i * 4
            print(f"{GLYPHS[glyph_index]} ", end="")

        print(f"\033[0m", end="")
        print(f"| 0x{value:0{8}x}")
        print(f"\033[{cursor_xy[0]};{cursor_xy[1]}H", end="")

    def execute(self, program: list[int]):
        READ = 0
        WRITE = 1

        CRT_PC_POS = 34
        CRT_IR_POS = 35
        CRT_ACC_POS = 36

        self.program = program

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
        data_tx = self.program[address]

        # hide cursor
        print("\033[?25l", end="")

        # clear terminal
        print("\033[1;1H\033[2J", end="")
        self.draw_crt()
        self.update_crt_line(CRT_PC_POS, 0)
        self.update_crt_line(CRT_IR_POS, 0)
        self.update_crt_line(CRT_ACC_POS, 0)

        while True:
            print("\033[38;1H", end="") # move cursor to bottom of crt

            self.send_32b_ptp_a(data_tx)
            self._pulse_clock(1)

            rw_intent = self.baby_ram_rw

            if self.baby_stop_lamp == 1:
                break

            self.ptp_a_ctrl = 1
            self.ptp_a_ctrl = 0

            address, data_rx, pc, ir, acc = self.get_ptp_b_data()

            print(f"\ntick: {tick % 8} (total: {tick})")
            self.update_crt_line(CRT_PC_POS, pc)
            self.update_crt_line(CRT_IR_POS, ir)
            self.update_crt_line(CRT_ACC_POS, acc)
            tick += 1

            if rw_intent == READ:
                data_tx = self.program[address]
            elif rw_intent == WRITE:
                self.program[address] = data_rx
                self.update_crt_line(address, data_rx)

        # reveal cursor
        print(f"\033[?25h", end="")

        print(f"\n\nstop lamp: {self.baby_stop_lamp}")