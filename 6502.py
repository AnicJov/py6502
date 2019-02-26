from util import *
from threading import Thread
from ram import RAM


class CPU(Thread):

    def __init__(self, mode=0, frequency=1, rom_path="ROM/test12.bin", ram=None):

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
        self.SP = 0b0000000111111111        # Stack Pointer

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
        sp = bfmt(self.SP, 16)
        pc = bfmt(self.PC, 16)
        flg = bfmt(self.flags)
        run = "True " if self.running else "False"
        mode = "Async" if self.mode == 0 else "Step "

        state = "+=================" + "===========================+\n"\
                "|          CPU: " + self.name + "          |\n"\
                "+=================+" + "==========================+\n"\
                "| AX |  " + bfmt(self.AX) + "  | SP |  " + sp[:8] + " " + sp[8:] + "  |\n"\
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
        if check_bit(self.flags, 4):
            if self.mode != 0:
                input()
            self.running = False
            clear()
            print(self)
            input("<Breakpoint>")
            self.running = True
            clear()
            print(self)
        else:
            if self.mode != 0:
                input()

    def load_rom(self, path):
        with open(path, 'rb') as rom:
            self.rom = rom.read().strip(b'\n')

    def decode_instruction(self, instruction):
        try:
            opcode = instruction[0]
            print("Current instruction: $", end='')
            print(hfmt(instruction[0]))

            #           LDA Immediate
            if opcode == 0xa9:
                self.lda_im(instruction[1])
            #           LDA Indirect,X
            if opcode == 0xa1:
                self.lda_indx(instruction[1])
            #           LDA Indirect,Y
            if opcode == 0xb1:
                self.lda_indy(instruction[1])
            #           LDX Immediate
            if opcode == 0xa2:
                self.ldx_im(instruction[1])
            #           LDY Immediate
            if opcode == 0xa0:
                self.ldy_im(instruction[1])
            #           STA Zero Page
            if opcode == 0x85:
                self.sta_zp(instruction[1])
            #           STA Absolute
            if opcode == 0x8d:
                self.sta_abs(hcat(instruction[2], instruction[1]))
            #           STA Absolute,Y
            if opcode == 0x99:
                self.sta_absy(hcat(instruction[2], instruction[1]))
            #           STA Indirect,X
            if opcode == 0x81:
                self.sta_indx(instruction[1])
            #           STX Absolute
            if opcode == 0x8e:
                self.stx_abs(hcat(instruction[2], instruction[1]))
            #           STY Absolute
            if opcode == 0x8c:
                self.sty_abs(hcat(instruction[2], instruction[1]))
            #           TAX Implied
            if opcode == 0xaa:
                self.tax()
            #           TXA Implied
            if opcode == 0x8a:
                self.txa()
            #           INX Implied
            if opcode == 0xe8:
                self.inx()
            #           INY Implied
            if opcode == 0xc8:
                self.iny()
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
            #           CPY Immediate
            if opcode == 0xc0:
                self.cpy_im(instruction[1])
            #           JMP Absolute
            if opcode == 0x4c:
                self.jmp_abs(hcat(instruction[2], instruction[1]))
            #           JMP Indirect
            if opcode == 0x6c:
                self.jmp_ind(hcat(instruction[2], instruction[1]))
            #           JSR Absolute
            if opcode == 0x20:
                self.jsr_abs(hcat(instruction[2], instruction[1]))
            #           RTS Implied
            if opcode == 0x60:
                self.rts()
            #           PHA Implied
            if opcode == 0x48:
                self.pha()
            #           PLA Implied
            if opcode == 0x68:
                self.pla()

        except IndexError:
            # Stop running and set the break flag
            self.running = False
            self.flags = set_bit(self.flags, 4)

            # Refresh UI
            clear()
            print(self)

            print("End of ROM")
            input("Press <Enter> to exit...")
            exit()

    # -- Processor state checks --

    def zero_check(self, val):
        if val == 0:
            self.flags = set_bit(self.flags, 1, 1)
        else:
            self.flags = set_bit(self.flags, 1, 0)

    def negative_check(self, val):
        if check_bit(val, 7):
            self.flags = set_bit(self.flags, 7, 1)
        else:
            self.flags = set_bit(self.flags, 7, 0)

    def carry_check(self, val):
        if val > 255:
            self.flags = set_bit(self.flags, 0, 1)
        else:
            self.flags = set_bit(self.flags, 0, 0)

    def overflow_check(self, val1, val2):
        print(val1, val2)
        val_sum = val1 + val2
        if check_bit(val1, 7) and check_bit(val2, 7) and (not check_bit(val_sum, 7)):
            self.flags = set_bit(self.flags, 6)
        elif (not check_bit(val1, 7)) and (not check_bit(val2, 7)) and check_bit(val_sum, 7):
            self.flags = set_bit(self.flags, 6)
        else:
            self.flags = set_bit(self.flags, 6, 0)

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

    # (Indirect,X)
    def lda_indx(self, ind_addr):
        print("LDA ($" + hfmt(ind_addr) + ",X)")

        # Get absolute address
        if ind_addr + self.X > 255:
            rel_addr = ind_addr + self.X - 255
        else:
            rel_addr = ind_addr + self.X

        addr = hcat(self.ram.read(rel_addr), self.ram.read(rel_addr + 1))

        # Set A to value in address
        self.AX = self.ram.read(addr)

        self.offset += 1

    # (Indirect),Y
    def lda_indy(self, ind_addr):
        print("LDA ($" + hfmt(ind_addr) + "),Y")

        # Get absolute address
        addr = hcat(self.ram.read(ind_addr + 1), self.ram.read(ind_addr)) + self.Y

        # Load value in address into A
        self.AX = self.ram.read(addr)

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

    # - LDY - Load Y Register
    # Immediate
    def ldy_im(self, val):
        print("LDY #$" + hfmt(val))

        self.Y = val
        # Set zero flag
        self.zero_check(val)
        # Set negative flag
        self.negative_check(val)

        self.offset += 1

    # - STA - Store Accumulator
    # Zero Page
    def sta_zp(self, addr):
        print("STA $" + hfmt(addr, 2))

        self.ram.write(addr, self.AX)
        self.offset += 1

    # Absolute
    def sta_abs(self, addr):
        print("STA $" + hfmt(addr, 4))

        self.ram.write(addr, self.AX)
        self.offset += 2

    # Absolute,Y
    def sta_absy(self, addr):
        print("STA $" + hfmt(addr, 4) + ",Y")

        addr = addr + self.Y

        self.ram.write(addr, self.AX)

        self.offset += 2

    # (Indirect,X)
    def sta_indx(self, ind_addr):
        print("STA ($" + hfmt(ind_addr) + ", X)")

        # Get absolute address
        if ind_addr + self.X > 255:
            rel_addr = ind_addr + self.X
        else:
            rel_addr = ind_addr + self.X - 255

        addr = hcat(self.ram.read(rel_addr), self.ram.read(rel_addr + 1))

        # Store value of A in the address
        self.ram.write(addr, self.AX)

        self.offset += 1

    # - STX - Store X Register
    # Absolute
    def stx_abs(self, addr):
        print("STX $" + hfmt(addr, 4))

        self.ram.write(addr, self.X)
        self.offset += 2

    # - STY - Store Y Register
    # Absolute
    def sty_abs(self, addr):
        print("STY $" + hfmt(addr, 4))

        self.ram.write(addr, self.Y)
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

    # - TXA - Transfer X to Accumulator
    # Implied
    def txa(self):
        print("TXA")

        self.AX = self.X
        # Set zero flag
        self.zero_check(self.AX)
        # Set negative flag
        self.negative_check(self.AX)

    # - INX - Increment X Register
    # Implied
    def inx(self):
        print("INX")

        self.X += 1
        # Set zero flag
        self.zero_check(self.X)
        # Set negative flag
        self.negative_check(self.X)

    # - INY - Increment Y Register
    # Implied
    def iny(self):
        print("INY")

        self.Y += 1
        # Set zero flag
        self.zero_check(self.Y)
        # Set negative flag
        self.negative_check(self.Y)

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
        self.ram.push(self.PC, self.SP)
        self.SP -= 1

        self.ram.push(self.flags, self.SP)
        self.SP -= 1

        # IRQ interrupt vector at $FFFE/F is loaded into the PC
        # |
        # v
        # self.PC = self.ram.read(0xFFFE)

        # Set break flag
        self.flags = set_bit(self.flags, 4, 1)

    # - BNE - Branch if Not Equal
    # Relative
    def bne(self, addr):
        print("BNE $" + hfmt(addr))

        # If zero bit is clear add relative displacement
        if not check_bit(self.flags, 1):
            # If number is negative subtract it's two's complement
            if check_bit(addr, 7):
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
            self.flags = set_bit(self.flags, 0, 1)
        else:
            self.flags = set_bit(self.flags, 0, 0)

        # If value of AX is equal to passed value, set zero flag
        if self.AX == val:
            self.flags = set_bit(self.flags, 1, 1)
        else:
            self.flags = set_bit(self.flags, 1, 0)

        # If bit 7 of the result is set, set negative flag
        self.negative_check(self.AX)

        self.offset += 1

    # - CPX - Compare X Register
    # Immediate
    def cpx_im(self, val):
        print("CPX #$" + hfmt(val))

        # If value of X is greater than passed value, set carry flag
        if self.X >= val:
            self.flags = set_bit(self.flags, 0, 1)
        else:
            self.flags = set_bit(self.flags, 0, 0)

        # If value of X is equal to passed value, set zero flag
        if self.X == val:
            self.flags = set_bit(self.flags, 1, 1)
        else:
            self.flags = set_bit(self.flags, 1, 0)

        # If bit 7 of the result is set, set negative flag
        self.negative_check(self.X)

        self.offset += 1

    # - CPY - Compare Y Register
    # Immediate
    def cpy_im(self, val):
        print("CPY #$" + hfmt(val))

        # If value of Y is greater than passed value, set carry flag
        if self.Y >= val:
            self.flags = set_bit(self.flags, 0, 1)
        else:
            self.flags = set_bit(self.flags, 0, 0)

        # If value of Y is equal to passed value, set zero flag
        if self.Y == val:
            self.flags = set_bit(self.flags, 1, 1)
        else:
            self.flags = set_bit(self.flags, 1, 0)

        # If bit 7 of the result is set, set negative flag
        self.negative_check(self.Y)

        self.offset += 1

    # - JMP - Jump
    # Absolute
    def jmp_abs(self, addr):
        print("JMP $" + hfmt(addr, 4))

        self.PC = addr - 1

    # Indirect
    def jmp_ind(self, ind_addr):
        print("JMP ($" + hfmt(ind_addr, 4) + ")")

        # Fetch the target address
        addr = hcat(self.ram.read(ind_addr), self.ram.read(ind_addr + 1))

        # Set the program counter to that address
        self.PC = addr

    # - JSR - Jump to Subroutine
    def jsr_abs(self, addr):
        print("JSR $" + hfmt(addr, 4))

        self.ram.push(self.PC + 2, self.SP)
        self.PC = addr - 1

    # - RTS - Return from Subroutine
    def rts(self):
        print("RTS")

        self.PC = self.ram.pop(self.SP)

    # - PHA - Push Accumulator
    # Implied
    def pha(self):
        print("PHA")

        self.ram.push(self.AX, self.SP)
        self.SP -= 1

    # - PLA - Pull Accumulator
    # Implied
    def pla(self):
        print("PLA")

        self.AX = self.ram.pop(self.SP + 1)
        self.SP += 1


if __name__ == "__main__":
    cpu = CPU(mode=1, frequency=0)
    clear()
    print(cpu)
    print("6502 Emulator by Andrija Jovanovic\n")
    print("Running ROM:")
    print(cpu.rom_path, "-", cpu.rom)
    input("\nPress <Enter> to start...")
    cpu.run()
