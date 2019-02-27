from cpu import CPU
from ppu import PPU
from util import *
import sys


def main():
    if len(sys.argv) >= 2:
        if sys.argv[1] == "noconsole":
            cpu = CPU(mode=0, frequency=0, console=False)
        else:
            cpu = None
    else:
        cpu = CPU(mode=0, frequency=0, console=True)

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
