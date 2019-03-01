from cpu import CPU
from ppu import PPU
from util import *
import sys


def main():
    mode = 0
    frequency = 0

    if len(sys.argv) >= 2:
        if sys.argv[1] == "noconsole":
            cpu = CPU(mode=mode, frequency=frequency, console=False)
        else:
            cpu = None
    else:
        cpu = CPU(mode=mode, frequency=frequency, console=True)

    if sys.platform == "win32":
        ppu = PPU(cpu)
        ppu.start()

    clear()
    print(cpu)
    print("6502 Emulator by Andrija Jovanovic\n")
    print("Running ROM: ", end='')
    print(cpu.rom_path)
    input("\nPress <Enter> to start...")
    cpu.start()


if __name__ == '__main__':
    main()
