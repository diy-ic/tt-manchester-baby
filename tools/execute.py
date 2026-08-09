import programs
from manchesterbaby import ManchesterBaby

from ttboard.demoboard import DemoBoard, RPMode

def main():
    tt = DemoBoard.get()

    if not tt.shuttle.has("tt_um_krisjdev_manchester_baby"):
        print("shuttle doesn't contain manchester baby project")
        return False

    tt.shuttle.tt_um_krisjdev_manchester_baby.enable()
    tt.mode = RPMode.ASIC_RP_CONTROL

    baby = ManchesterBaby()

    baby.execute(programs.get("sample"))


if __name__ == "__main__":
    main()