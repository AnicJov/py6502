from util import *
from threading import Thread
from ram import RAM


class CPU(Thread):

    def __init__(self, mode=0, frequency=1, rom_path="ROM/test7.bin", ram=None):

        # -- Threading --
        Thread.__init__(self)

        # -- RAM --
        if ram is None:
            self.ram = RAM()
        else:
            self.ram = ram

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
        self.flags = 0b00100000             # Processor flags

        # -- Other --

        self.name = "MOS Technology 6502"   # Full name of the processor
        self.frequency = frequency          # Working frequency in Hz
        self.running = False                # If true, execute instructions
        self.mode = mode                    # 0 for Asynchronous, 1 for Step
        self.rom_path = rom_path            # Path to a ROM
        self.offset = 0                     # Memory offset of the program
        self.rom = None                     # ROM binary information

        self.load_rom(self.rom_path)        # Sets the rom field to file contents

    def __repr__(self):
        sp = bfmt(self.SP[0]) + " " + bfmt(self.SP[1])
        pc = bfmt(self.PC, 16)
        flg = bfmt(self.flags)
        run = "True " if self.running else "False"
        mode = "Async" if self.mode == 0 else "Step "

        state = "+=================" + "===========================+\n"\
                "|          CPU: " + self.name + "          |\n"\
                "+=================+" + "==========================+\n"\
                "| AX |  " + bfmt(self.AX) + "  | SP |  " + sp + "  |\n"\
                "+-----------------+" + "--------------------------+\n"\
                "|  X |  " + bfmt(self.X) + "  | PC |  " + pc[:8] + " " + pc[8:] + "  |\n"\
                "+-----------------+" + "--------------------------+\n"\
                "|  Y |  " + bfmt(self.Y) + "  | Flags |        " + flg + "  |\n"\
                "+=================+" + "================||||||||==+\n"\
                "| Running: " + run + "  | Mode: " + mode + " |  NV-BDIZC  |\n"\
                "+=================+" + "==========================+\n"

        # | Uncomment for a memory dump in case of debugging
        # v
        # self.ram.dump_heap()

        return state + "\n" + str(self.ram)

    def run(self):
        self.running = True

        if self.mode == 0:
            while self.running:
                freq(self.tick, self.frequency)
        else:
            while self.running:
                self.tick()

    def tick(self):
        self.PC += self.offset
        index = self.PC
        self.offset = 0

        clear()
        print(self)

        self.decode_instruction(self.rom[index:index+3])
        self.PC += 1

        # In case of interrupt
        if self.flags & 0b00010000:
            self.running = False
            input("<Interrupt>")
            clear()
            print(self)
            input("Press <Enter> to exit...")
            exit()
        else:
            if self.mode != 0:
                input()

    def load_rom(self, path):
        with open(path, 'rb') as rom:
            self.rom = rom.read()

    def decode_instruction(self, instruction):
        try:
            opcode = instruction[0]
            print("Current instruction: 0x", end='')
            print(hfmt(instruction[0]))

            #           LDA Immediate
            if opcode == 0xa9:
                self.lda_im(instruction[1])
            #           LDX Immediate
            if opcode == 0xa2:
                self.ldx_im(instruction[1])
            #           STA Absolute
            if opcode == 0x8d:
                self.sta_abs(instruction[1] + instruction[2])
            #           STA Zero Page
            if opcode == 0x85:
                self.sta_zp(instruction[1])
            #           STX Absolute
            if opcode == 0x8e:
                self.stx_abs(instruction[1] + instruction[2])
            #           TAX Implied
            if opcode == 0xaa:
                self.tax()
            #           INX Implied
            if opcode == 0xe8:
                self.inx()
            #           DEX Implied
            if opcode == 0xca:
                self.dex()
            #           ADC Immediate
            if opcode == 0x69:
                self.adc_im(instruction[1])
            #           ADC Zero Page
            if opcode == 0x65:
                self.adc_zp(instruction[1])
            #           BRK Implied
            if opcode == 0x00:
                self.brk()
            #           BNE Relative
            if opcode == 0xd0:
                self.bne(instruction[1])
            #           CMP Immediate
            if opcode == 0xc9:
                self.cmp_im(instruction[1])
            #           CPX Immediate
            if opcode == 0xe0:
                self.cpx_im(instruction[1])
            #           JMP Indirect
            if opcode == 0x6c:
                self.jmp_ind(instruction[1] + instruction[2])

        except IndexError:
            # Stop running and set the break flag
            self.running = False
            self.flags = self.flags ^ 0b00010000

            # Refresh UI
            clear()
            print(self)

            print("End of ROM")
            input("Press <Enter> to exit...")
            exit()

    # -- Processor state checks --

    def zero_check(self, val):
        if val == 0:
            self.flags = self.flags | 0b00000010
        else:
            self.flags = self.flags & 0b11111101

    def negative_check(self, val):
        if val & 0b10000000:
            self.flags = self.flags | 0b10000000
        else:
            self.flags = self.flags & 0b01111111

    def carry_check(self, val):
        if val > 255:
            self.flags = self.flags | 0b00000001
        else:
            self.flags = self.flags & 0b11111110

    def overflow_check(self, val1, val2):
        print(val1, val2)
        val_sum = val1 + val2
        if (val1 & 0b10000000) and (val2 & 0b10000000) and (not (val_sum & 0b10000000)):
            self.flags = self.flags | 0b01000000
        elif (not (val1 & 0b10000000)) and (not (val2 & 0b10000000)) and (val_sum & 0b10000000):
            self.flags = self.flags | 0b01000000
        else:
            self.flags = self.flags & 0b10111111

    # -- Instructions --

    # - LDA - Load Accumulator -
    # Immediate
    def lda_im(self, val):
        print("LDA #$" + hfmt(val))

        self.AX = val
        # Set zero flag
        self.zero_check(val)
        # Set negative flag
        self.negative_check(val)

        self.offset += 1

    # - LDX - Load X Register
    # Immediate
    def ldx_im(self, val):
        print("LDX #$" + hfmt(val))

        self.X = val
        # Set zero flag
        self.zero_check(val)
        # Set negative flag
        self.negative_check(val)

        self.offset += 1

    # - STA - Store Accumulator
    # Absolute
    def sta_abs(self, addr):
        print("STA $" + hfmt(addr, 4))

        self.ram.write(addr, self.AX)
        self.offset += 2

    # Zero Page
    def sta_zp(self, addr):
        print("STA $" + hfmt(addr, 2))

        self.ram.write(addr, self.AX)
        self.offset += 1

    # - STX - Store X Register
    # Absolute
    def stx_abs(self, addr):
        print("STX $" + hfmt(addr, 4))

        self.ram.write(addr, self.X)
        self.offset += 2

    # - TAX - Transfer Accumulator to X
    # Implied
    def tax(self):
        print("TAX")

        self.X = self.AX
        # Set zero flag
        self.zero_check(self.X)
        # Set negative flag
        self.negative_check(self.X)

    # - INX - Increment X Register
    # Implied
    def inx(self):
        print("INX")

        self.X += 1
        # Set zero flag
        self.zero_check(self.X)
        # Set negative flag
        self.negative_check(self.X)

    # - DEX - Decrement X Register
    # Implied
    def dex(self):
        print("DEX")

        self.X -= 1
        # Set zero flag
        self.zero_check(self.X)
        # Set negative flag
        self.negative_check(self.X)

    # - ADC - Add with Carry
    # Immediate
    def adc_im(self, val):
        print("ADC #$" + hfmt(val, 2))

        result = self.AX + val
        result_8 = result - 0b100000000

        # Set carry flag
        self.carry_check(result)
        # Set zero flag
        self.zero_check(result_8)
        # Set overflow flag
        self.overflow_check(self.AX, val)
        # Set negative flag
        self.negative_check(result_8)

        self.AX = result_8
        self.offset += 1

    # Zero Page
    def adc_zp(self, addr):
        print("ADC $" + hfmt(addr, 2))

        val = self.ram.read(addr)

        result = self.AX + val
        result_8 = result - 0b100000000

        # Set carry flag
        self.carry_check(result)
        # Set zero flag
        self.zero_check(result_8)
        # Set overflow flag
        self.overflow_check(self.AX, val)
        # Set negative flag
        self.negative_check(result_8)

        self.AX = result_8
        self.offset += 1

    # - BRK - Force Interrupt
    # Implied
    def brk(self):
        print("BRK")

        # Push program counter and processor status
        self.ram.push(self.PC)
        self.ram.push(self.flags)

        # IRQ interrupt vector at $FFFE/F is loaded into the PC
        self.PC = self.ram.read(0xFFFE)

        # Set break flag
        self.flags = self.flags ^ 0b00010000

    # - BNE - Branch if Not Equal
    # Relative
    def bne(self, addr):
        print("BNE $" + hfmt(addr))

        # If zero bit is clear add relative displacement
        if not (self.flags & 0b00000010):
            # If number is negative subtract it's two's complement
            if addr & 0b10000000:
                num = decomp(addr)
                self.PC -= num
            # If number is positive add it to the program counter
            else:
                self.PC += (addr + 1)
        else:
            self.offset += 1

    # - CMP - Compare
    # Immediate
    def cmp_im(self, val):
        print("CMP #$" + hfmt(val))

        # If value of AX is greater than passed value, set carry flag
        if self.AX >= val:
            self.flags = self.flags | 0b00000001
        else:
            self.flags = self.flags & 0b11111110

        # If value of AX is equal to passed value, set zero flag
        if self.AX == val:
            self.flags = self.flags | 0b00000010
        else:
            self.flags = self.flags & 0b11111101

        # If bit 7 of the result is set, set negative flag
        self.negative_check(self.AX)

        self.offset += 1

    # - CPX - Compare X Register
    # Immediate
    def cpx_im(self, val):
        print("CPX #$" + hfmt(val))

        # If value of X is greater than passed value, set carry flag
        if self.X >= val:
            self.flags = self.flags | 0b00000001
        else:
            self.flags = self.flags & 0b11111110

        # If value of X is equal to passed value, set zero flag
        if self.X == val:
            self.flags = self.flags | 0b00000010
        else:
            self.flags = self.flags & 0b11111101

        # If bit 7 of the result is set, set negative flag
        self.negative_check(self.X)

        self.offset += 1

    # - JMP - Jump
    # Indirect
    def jmp_ind(self, ind_addr):
        print("JMP ($" + hfmt(ind_addr, 4) + ")")

        # Fetch the target address
        addr = "0x" + hfmt(self.ram.read(ind_addr + 1)) + hfmt(self.ram.read(ind_addr))
        addr = int(addr, 16)

        # Set the program counter to that address
        self.PC = addr


if __name__ == "__main__":
    cpu = CPU(mode=1, frequency=0)
    clear()
    print(cpu)
    print("6502 Emulator by Andrija Jovanovic\n")
    print("Running ROM:")
    print(cpu.rom)
    input("\nPress <Enter> to start...")
    cpu.run()
