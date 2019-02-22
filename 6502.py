from util import *


class CPU:

    def __init__(self, mode=0, frequency=1, rom_path="ROM/test.bin"):

        # -- Registers --

        # - Main registers -
        self.AX = 0b00000000                # Accumulator

        # - Index registers -
        self.X = 0b00000000                 # X index
        self.Y = 0b00000000                 # Y index
        self.SP = [0b00000001, 0b00000000]  # Stack Pointer

        # - Program counter -
        self.PC = 0b0000000000000000        # Program Counter

        # - Status register -
        #
        # Legend:
        # N - Negative, V - Overflow, B - Breakpoint
        # D - BCD, I - Interrupt, Z - Zero, C - Carry
        #
        #              NV-BDIZC
        #              || |||||
        self.flags = 0b00000000             # Processor flags


        # -- Other --

        self.name = "MOS Technology 6502"   # Full name of the processor
        self.frequency = frequency          # Working frequency in Hz
        self.running = False                # If true, execute instructions
        self.mode = mode                    # 0 for Asynchronous, 1 for Step
        self.rom_path = rom_path            # Path to a ROM
        self.offset = 0

        self.load_rom(self.rom_path)


    def __repr__(self):
        SP = bfmt(self.SP[0]) + " " + bfmt(self.SP [1])
        PC = bfmt(self.PC)
        flg = bfmt(self.flags)
        run = "True " if self.running else "False"
        mode = "Async" if self.mode == 0 else "Step "

        state = "+=================" + "===========================+\n"\
                "|          CPU: " + self.name + "          |\n"\
                "+=================+" + "==========================+\n"\
                "| AX |  " + bfmt(self.AX) + "  | SP |  " + SP + "  |\n"\
                "+-----------------+" + "--------------------------+\n"\
                "|  X |  " + bfmt(self.X) + "  | PC |           " + PC + "  |\n"\
                "+-----------------+" + "--------------------------+\n"\
                "|  Y |  " + bfmt(self.Y) + "  | Flags |        " + flg + "  |\n"\
                "+=================+" + "================||||||||==+\n"\
                "| Running: " + run + "  | Mode: " + mode + " |  NV-BDIZC  |\n"\
                "+=================+" + "==========================+\n"

        return state

    def run(self):
        self.running = True

        if self.mode == 0:
            while self.running:
                freq(self.tick, self.frequency)
        else:
            while self.running:
                self.tick()

    def tick(self):
        clear()
        print(self)

        index = self.PC + self.offset

        self.decode_instruction(self.rom[index:index+3])
        self.PC += 1
        if self.mode != 0:
            input()

    def load_rom(self, path):
        with open(path, 'rb') as rom:
            self.rom = rom.read()

    def decode_instruction(self, instruction):
        try:
            print("Current instruction: ", end='')
            print(hfmt(instruction[0]))

            #           LDA Immediate
            if instruction[0] == 0xa9:
                self.lda(instruction[1])
            #           STA Absolute
            if instruction[0] == 0x8d:
                self.sta(instruction[1] + instruction[2])
        except IndexError:
            print("End of ROM")
            input("Press <Enter> to exit...")
            exit()

    # -- Instructions --

    # - LDA - Load Accumulator -
    # Immediate
    def lda(self, val):
        print("LDA #0x" + hfmt(val))
        self.AX = val
        # Set zero flag
        if val == 0:
            self.flags = self.flags ^ 0b00000010
        # Set negative flag
        if val & 0b10000000:
            self.flags = self.flags ^ 0b10000000
        self.offset += 1

    # - STA - Store Accumulator
    # Absolute
    def sta(self, addr):
        print("STA $0x" + hfmt(addr, 4))
        self.offset += 2

if __name__ == "__main__":
    cpu = CPU(mode=1)
    clear()
    print(cpu)
    print("6502 Emulator by Andrija Jovanovic\n")
    print("Running ROM:")
    print(cpu.rom)
    input("\nPress <Enter> to start...")
    cpu.run()
