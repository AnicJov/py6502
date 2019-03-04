# TODO: Add file headers

from util import *
from threading import Thread
from ram import RAM
from random import randint


class CPU(Thread):

    def __init__(self, mode=0, frequency=1, rom_path="ROM/snake.bin", ram=None, console=True):

        """

            -- Threading --

        """
        Thread.__init__(self)

        """
        
            -- RAM --
            
        """
        if ram is None:
            self.ram = RAM()
        else:
            self.ram = ram

        """
        
            -- Registers --
            
        """

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

        """
        
            -- Other --
            
        """

        self.name = "MOS Technology 6502"   # Full name of the processor
        self.frequency = frequency          # Working frequency in Hz
        self.running = False                # If true, execute instructions
        self.mode = mode                    # 0 for Asynchronous, 1 for Step
        self.rom_path = rom_path            # Path to a ROM
        self.offset = 0                     # Memory offset of the program
        self.rom = None                     # ROM binary information
        self.console = console              # If true prints CPU and RAM info every tick
        self.lookup_table = []              # Maps bytes to instructions

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
        """ Starts the clock and starts executing instructions """

        # Sets up instruction lookup table
        self.setup_lookup_table()

        # Sets the rom field to file contents
        self.load_rom(self.rom_path)

        self.running = True

        # For snake.bin, sets the lastKey variable to key_D
        self.ram.write(0xff, 0x64)

        # Starting address of program
        self.PC = 0x0600

        # Runs tick at a certain frequency if mode is 0,
        # or as fast as possible if mode is something else
        if self.mode == 0:
            while self.running:
                freq(self.tick, self.frequency)
        else:
            while self.running:
                self.tick()

    def tick(self):
        """ Fetches instruction, executes it and progresses the program counter """

        # Generate random number in memory location 0xFE for use in programs
        self.ram.write(0xfe, randint(0, 255))

        # Offset the program counter
        self.PC += self.offset
        index = self.PC
        self.offset = 0

        # Print UI into console
        if self.console:
            clear()
            print(self)

        # Run instructions
        self.decode_instruction(self.ram.heap[index:index+3])

        # Progress the program counter
        self.PC += 1

        # In case of interrupt
        if check_bit(self.flags, 4):
            if self.mode != 0:
                input()
            self.running = False
            if self.console:
                clear()
                print(self)
            input("<Breakpoint>")
            self.running = True
            if self.console:
                clear()
                print(self)
        else:
            if self.mode != 0:
                input()

    def load_rom(self, path):
        """ Loads a file specified in <path> into memory starting from address 0x0600 """

        with open(path, 'rb') as rom:
            i = 0

            for byte in rom.read():
                self.ram.write(0x0600 + i, byte)
                i += 1

    def setup_lookup_table(self):
        self.lookup_table = [None] * 0x100

        self.lookup_table[0xEA] = lambda: self.nop(self.implied())

        self.lookup_table[0xA9] = lambda: self.lda(self.immediate())
        self.lookup_table[0xA5] = lambda: self.lda(self.zero_page())
        self.lookup_table[0xB5] = lambda: self.lda(self.zero_page_x())
        self.lookup_table[0xA1] = lambda: self.lda(self.indirect_x())
        self.lookup_table[0xB1] = lambda: self.lda(self.indirect_y())

        self.lookup_table[0xA2] = lambda: self.ldx(self.immediate())
        self.lookup_table[0xA6] = lambda: self.ldx(self.zero_page())

        self.lookup_table[0xA0] = lambda: self.ldy(self.immediate())

        self.lookup_table[0x4A] = lambda: self.lsr_acc()
        self.lookup_table[0x46] = lambda: self.lsr_zp(self.PC + 1)
        self.lookup_table[0x4E] = lambda: self.lsr_abs(hcat(self.PC + 2, self.PC + 1))

        self.lookup_table[0xE9] = lambda: self.sbc(self.immediate())
        self.lookup_table[0xE5] = lambda: self.sbc(self.zero_page())
        self.lookup_table[0xED] = lambda: self.sbc(self.absolute())

        self.lookup_table[0x38] = lambda: self.sec(self.implied())

        self.lookup_table[0x85] = lambda: self.sta_zp(self.PC + 1)

    def decode_instruction(self, instruction):
        """ Looks up instruction in memory and calls the appropriate function """

        try:
            opcode = instruction[0]

            if self.console:
                print("Current instruction: $", end='')
                print(hfmt(opcode))

            # TODO: Make this a lookup table instead of conditions

            try:
                self.lookup_table[opcode]()
            except TypeError:
                self.unk(opcode)

            #           STA Zero Page,X
            if opcode == 0x95:
                self.sta_zpx(instruction[1])
            #           STA Absolute
            if opcode == 0x8d:
                self.sta_abs(hcat(instruction[2], instruction[1]))
            #           STA Absolute,Y
            if opcode == 0x99:
                self.sta_absy(hcat(instruction[2], instruction[1]))
            #           STA Indirect,X
            if opcode == 0x81:
                self.sta_indx(instruction[1])
            #           STA Indirect,Y
            if opcode == 0x91:
                self.sta_indy(instruction[1])
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
            #           INC Zero Page
            if opcode == 0xe6:
                self.inc_zp(instruction[1])
            #           INX Implied
            if opcode == 0xe8:
                self.inx()
            #           INY Implied
            if opcode == 0xc8:
                self.iny()
            #           DEC Zero Page
            if opcode == 0xc6:
                self.dec_zp(instruction[1])
            #           DEC Absolute
            if opcode == 0xce:
                self.dec_abs(hcat(instruction[2], instruction[1]))
            #           DEX Implied
            if opcode == 0xca:
                self.dex()
            #           AND Immediate
            if opcode == 0x29:
                self.and_im(instruction[1])
            #           ADC Immediate
            if opcode == 0x69:
                self.adc_im(instruction[1])
            #           ADC Zero Page
            if opcode == 0x65:
                self.adc_zp(instruction[1])
            #           BIT Zero Page
            if opcode == 0x24:
                self.bit_zp(instruction[1])
            #           BIT Absolute
            if opcode == 0x2c:
                self.bit_abs(hcat(instruction[2], instruction[1]))
            #           BRK Implied
            if opcode == 0x00:
                self.brk()
            #           BCC Relative
            if opcode == 0x90:
                self.bcc(instruction[1])
            #           BCS Relative
            if opcode == 0xb0:
                self.bcs(instruction[1])
            #           BEQ Relative
            if opcode == 0xf0:
                self.beq(instruction[1])
            #           BNE Relative
            if opcode == 0xd0:
                self.bne(instruction[1])
            #           BRL Relative
            if opcode == 0x10:
                self.bpl(instruction[1])
            #           CLC Implied
            if opcode == 0x18:
                self.clc()
            #           CMP Immediate
            if opcode == 0xc9:
                self.cmp_im(instruction[1])
            #           CMP Zero Page
            if opcode == 0xc5:
                self.cmp_zp(instruction[1])
            #           CPX Immediate
            if opcode == 0xe0:
                self.cpx_im(instruction[1])
            #           CPX Zero Page
            if opcode == 0xe4:
                self.cpx_zp(instruction[1])
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

    """
    
        -- Processor state checks --
        
    """

    def zero_check(self, val):
        """ Sets zero flag appropriately for the value <val> passed """

        if val == 0:
            self.flags = set_bit(self.flags, 1, 1)
        else:
            self.flags = set_bit(self.flags, 1, 0)

    def negative_check(self, val):
        """ Sets negative flag appropriately for the value <val> passed """

        if check_bit(val, 7):
            self.flags = set_bit(self.flags, 7, 1)
        else:
            self.flags = set_bit(self.flags, 7, 0)

    def carry_check(self, val):
        """ Sets carry flag appropriately for the value <val> passed """

        if val > 255:
            self.flags = set_bit(self.flags, 0, 1)
        else:
            self.flags = set_bit(self.flags, 0, 0)

    def overflow_check(self, val1, val2):
        """ Sets overflow flag appropriately for the values <val1> and <val2> passed """

        val_sum = val1 + val2
        if check_bit(val1, 7) and check_bit(val2, 7) and (not check_bit(val_sum, 7)):
            self.flags = set_bit(self.flags, 6)
        elif (not check_bit(val1, 7)) and (not check_bit(val2, 7)) and check_bit(val_sum, 7):
            self.flags = set_bit(self.flags, 6)
        else:
            self.flags = set_bit(self.flags, 6, 0)

    """
    
        -- Addressing Modes --
    
    """

    def implied(self):
        self.offset += 0

        return None

    def implicit(self):
        self.offset += 0

        return None

    def accumulator(self):
        self.offset += 0

        return None

    def immediate(self):
        self.offset += 1

        return self.ram.read(self.PC + 1)

    def zero_page(self):
        self.offset += 1

        return self.ram.read(self.PC + 1)

    def zero_page_x(self):
        rel_addr = self.ram.read(self.PC + 1)

        if rel_addr + self.X > 255:
            addr = rel_addr + self.X - 255
        else:
            addr = rel_addr + self.X

        self.offset += 1

        return self.ram.read(addr)

    def zero_page_y(self):
        rel_addr = self.ram.read(self.PC + 1)

        if rel_addr + self.Y > 255:
            addr = rel_addr + self.Y - 255
        else:
            addr = rel_addr + self.Y

        self.offset += 1

        return self.ram.read(addr)

    def relative(self):
        self.offset += 1

        return self.ram.read(self.PC + 1)

    def absolute(self):
        addr = hcat(self.ram.read(self.PC + 2), self.ram.read(self.PC + 1))

        self.offset += 2

        return self.ram.read(addr)

    def absolute_x(self):
        addr = hcat(self.ram.read(self.PC + 2), self.ram.read(self.PC + 1)) + self.X

        self.offset += 2

        return self.ram.read(addr)

    def absolute_y(self):
        addr = hcat(self.ram.read(self.PC + 2), self.ram.read(self.PC + 1)) + self.Y

        self.offset += 2

        return self.ram.read(addr)

    def indirect(self):
        addr = hcat(self.ram.read(self.PC + 2), self.ram.read(self.PC + 1))

        self.offset += 2

        return self.ram.read(hcat(self.ram.read(addr), self.ram.read(addr + 1)))

    def indirect_x(self):
        ind_addr = hcat(self.ram.read(self.PC + 2), self.ram.read(self.PC + 1))

        if ind_addr + self.X > 255:
            rel_addr = ind_addr + self.X - 255
        else:
            rel_addr = ind_addr + self.X

        addr = hcat(self.ram.read(rel_addr), self.ram.read(rel_addr + 1))

        self.offset += 1

        return self.ram.read(addr)

    def indirect_y(self):
        addr = hcat(self.ram.read(self.ram.read(self.PC + 2) + 1), self.ram.read(self.ram.read(self.PC + 1))) + self.Y

        self.offset += 1

        return self.ram.read(addr)

    """
    
        -- Instructions --
        
    """

    # TODO: Make addressing modes separate functions and pass the return into
    #       specific instruction functions

    """ - UNK - Unknown Instruction """
    def unk(self, opcode):
        print("UNK $" + hfmt(opcode))

        self.offset += 0

    """ - NOP - No Operation """
    def nop(self, val):
        print("NOP")

        self.offset += 0

    """ - LDA - Load Accumulator - """
    def lda(self, val):
        print("LDA #$" + hfmt(val))

        self.AX = val

        # Set zero flag
        self.zero_check(val)
        # Set negative flag
        self.negative_check(val)

    """ - LDX - Load X Register """
    def ldx(self, val):
        print("LDX #$" + hfmt(val))

        self.X = val
        # Set zero flag
        self.zero_check(val)
        # Set negative flag
        self.negative_check(val)

    """ - LDY - Load Y Register """
    def ldy(self, val):
        print("LDY #$" + hfmt(val))

        self.Y = val
        # Set zero flag
        self.zero_check(val)
        # Set negative flag
        self.negative_check(val)

    """ - LSR - Logical Shift Right """
    # Accumulator
    def lsr_acc(self):
        print("LSR")

        self.flags = set_bit(self.flags, 0, check_bit(self.AX, 0))
        self.AX = self.AX >> 1

    def lsr_zp(self, addr):
        print("LSR $" + hfmt(addr))

        val = self.ram.read(addr)

        self.flags = set_bit(self.flags, 0, check_bit(val, 0))
        self.ram.write(addr, val >> 1)

    # Absolute
    def lsr_abs(self, addr):
        print("LSR $" + hfmt(addr, 4))

        val = self.ram.read(addr)

        self.flags = set_bit(self.flags, 0, check_bit(val, 0))
        self.ram.write(addr, val >> 1)

    """ - SBC - Subtract with Carry """
    def sbc(self, val):
        print("SBC #$")

        result, carry = bsub(self.AX, val)
        result, carry = bsub(result, check_bit(self.flags, 0))

        # Set carry flag
        if carry:
            self.flags = set_bit(self.flags, 0, 1)
        else:
            self.flags = set_bit(self.flags, 0, 0)
        # Set zero flag
        self.zero_check(result)
        # Set overflow flag
        self.overflow_check(self.AX, val)
        # Set negative flag
        self.negative_check(result)

        self.AX = result

    """ - SEC - Set Carry Flag """
    def sec(self, val):
        print("SEC")

        self.flags = set_bit(self.flags, 0, 1)

    """ - STA - Store Accumulator """
    # Zero Page
    def sta_zp(self, addr):
        print("STA $" + hfmt(addr, 2))

        self.ram.write(addr, self.AX)
        self.offset += 1

    # Zero Page,X
    def sta_zpx(self, ind_addr):
        print("STA $" + hfmt(ind_addr, 2))

        # Get absolute address
        if ind_addr + self.X > 255:
            addr = ind_addr + self.X
        else:
            addr = ind_addr + self.X - 255

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

    # (Indirect),Y
    def sta_indy(self, ind_addr):
        print("STA ($" + hfmt(ind_addr) + "),Y")

        # Get absolute address
        addr = hcat(self.ram.read(ind_addr + 1), self.ram.read(ind_addr)) + self.Y

        # Store value of A into memory
        self.ram.write(addr, self.AX)

        self.offset += 1

    """ - STX - Store X Register """
    # Absolute
    def stx_abs(self, addr):
        print("STX $" + hfmt(addr, 4))

        self.ram.write(addr, self.X)
        self.offset += 2

    """ - STY - Store Y Register """
    # Absolute
    def sty_abs(self, addr):
        print("STY $" + hfmt(addr, 4))

        self.ram.write(addr, self.Y)
        self.offset += 2

    """ - TAX - Transfer Accumulator to X """
    # Implied
    def tax(self):
        print("TAX")

        self.X = self.AX
        # Set zero flag
        self.zero_check(self.X)
        # Set negative flag
        self.negative_check(self.X)

    """ - TXA - Transfer X to Accumulator """
    # Implied
    def txa(self):
        print("TXA")

        self.AX = self.X

        # Set zero flag
        self.zero_check(self.AX)
        # Set negative flag
        self.negative_check(self.AX)

    """ - INC - Increment Memory """
    # Base
    def inc(self, val, addr):
        self.ram.write(addr, badd(val, 1)[0])

        # Set zero flag
        self.zero_check(val)
        # Set negative flag
        self.negative_check(val)

    # Zero Page
    def inc_zp(self, addr):
        print("INC $" + hfmt(addr))

        val = self.ram.read(addr)

        self.inc(val, addr)

        self.offset += 1

    """ - INX - Increment X Register """
    # Implied
    def inx(self):
        print("INX")

        self.X = badd(self.X, 1)[0]

        # Set zero flag
        self.zero_check(self.X)
        # Set negative flag
        self.negative_check(self.X)

    """ - INY - Increment Y Register """
    # Implied
    def iny(self):
        print("INY")

        self.Y = badd(self.Y, 1)[0]

        # Set zero flag
        self.zero_check(self.Y)
        # Set negative flag
        self.negative_check(self.Y)

    """ - DEC - Decrement Memory """
    # Zero Page
    def dec_zp(self, addr):
        print("DEC $" + hfmt(addr))

        val = self.ram.read(addr) - 1

        if val < 0:
            self.ram.write(addr, 255)
        else:
            self.ram.write(addr, val)

        self.offset += 1

    # Absolute
    def dec_abs(self, addr):
        print("DEC $" + hfmt(addr, 4))

        val = self.ram.read(addr) - 1

        if val < 0:
            self.ram.write(addr, 255)
        else:
            self.ram.write(addr, val)

        self.offset += 2

    """ - DEX - Decrement X Register """
    # Implied
    def dex(self):
        print("DEX")

        if self.X - 1 < 0:
            self.X = 255
        else:
            self.X -= 1

        # Set zero flag
        self.zero_check(self.X)
        # Set negative flag
        self.negative_check(self.X)

    """ - AND - Logical AND """
    # Immediate
    def and_im(self, val):
        print("AND $" + hfmt(val))

        self.AX = self.AX & val

        self.zero_check(self.AX)
        self.negative_check(self.AX)

        self.offset += 1

    """ - ADC - Add with Carry """
    # Base
    def adc(self, val):
        result, carry = badd(self.AX, val, check_bit(self.flags, 0))

        # Set carry flag
        if carry:
            self.flags = set_bit(self.flags, 0, 1)
        else:
            self.flags = set_bit(self.flags, 0, 0)
        # Set zero flag
        self.zero_check(result)
        # Set overflow flag
        self.overflow_check(self.AX, val)
        # Set negative flag
        self.negative_check(result)

        self.AX = result

    # Immediate
    def adc_im(self, val):
        print("ADC #$" + hfmt(val, 2))

        self.adc(val)

        self.offset += 1

    # Zero Page
    def adc_zp(self, addr):
        print("ADC $" + hfmt(addr, 2))

        val = self.ram.read(addr)

        self.adc(val)

        self.offset += 1

    """ - BIT - Bit Test """
    # Zero Page
    def bit_zp(self, addr):
        print("BIT $" + hfmt(addr))

        val = self.ram.read(addr)

        if self.AX & val == 0:
            self.flags = set_bit(self.flags, 1, 1)
        else:
            self.flags = set_bit(self.flags, 1, 0)

        self.flags = set_bit(self.flags, 6, check_bit(val, 6))
        self.flags = set_bit(self.flags, 7, check_bit(val, 7))

        self.offset += 1

    # Absolute
    def bit_abs(self, addr):
        print("BIT $" + hfmt(addr, 4))

        val = self.ram.read(addr)

        if self.AX & val == 0:
            self.flags = set_bit(self.flags, 2, 1)
        else:
            self.flags = set_bit(self.flags, 2, 0)

        self.flags = set_bit(self.flags, 6, check_bit(val, 6))
        self.flags = set_bit(self.flags, 7, check_bit(val, 7))

        self.offset += 2

    """ - BRK - Force Interrupt """
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

    """ - BCC - Branch if Carry Clear """
    def bcc(self, addr):
        print("BCC $" + hfmt(addr))

        # If carry bit is clear add relative displacement
        if not check_bit(self.flags, 0):
            # If number is negative subtract it's two's complement
            if check_bit(addr, 7):
                num = decomp(addr)
                self.PC -= num
            # If number is positive add it to the program counter
            else:
                self.PC += (addr + 1)
        else:
            self.offset += 1

    """ - BCS - Branch if Carry Set """
    # Relative
    def bcs(self, addr):
        print("BCS $" + hfmt(addr))

        # If carry bit is set add relative displacement
        if check_bit(self.flags, 0):
            # If number is negative subtract it's two's complement
            if check_bit(addr, 7):
                num = decomp(addr)
                self.PC -= num
            # If number is positive add it to the program counter
            else:
                self.PC += (addr + 1)
        else:
            self.offset += 1

    """ - BEQ - Branch if Equal """
    # Relative
    def beq(self, addr):
        print("BEQ $" + hfmt(addr))

        # If zero bit is set add relative displacement
        if check_bit(self.flags, 1):
            # If number is negative subtract it's two's complement
            if check_bit(addr, 7):
                num = decomp(addr)
                self.PC -= num
            # If number is positive add it to the program counter
            else:
                self.PC += (addr + 1)
        else:
            self.offset += 1

    """ - BNE - Branch if Not Equal """
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

    """ - BPL - Branch if Positive """
    # Relative
    def bpl(self, addr):
        print("BPL $" + hfmt(addr))

        # If negative bit is clear add relative displacement
        if not check_bit(self.flags, 7):
            # If number is negative subtract it's two's complement
            if check_bit(addr, 7):
                num = decomp(addr)
                self.PC -= num
            # If number is positive add it to the program counter
            else:
                self.PC += (addr + 1)
        else:
            self.offset += 1

    """ - CLC - Clear Carry Flag """
    # Implied
    def clc(self):
        print("CLC")

        self.flags = set_bit(self.flags, 0, 0)

    """ - CMP - Compare """
    # Base
    def cmp(self, val):
        result = bsub(self.AX, val)[0]

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
        self.flags = set_bit(self.flags, 7, check_bit(result, 7))

    # Immediate
    def cmp_im(self, val):
        print("CMP #$" + hfmt(val))

        self.cmp(val)

        self.offset += 1

    # Zero Page
    def cmp_zp(self, addr):
        print("CMP $" + hfmt(addr))

        val = self.ram.read(addr)

        self.cmp(val)

        self.offset += 1

    """ - CPX - Compare X Register """
    # Base
    def cpx(self, val):
        result = bsub(self.X, val)[0]

        # If value of AX is greater than passed value, set carry flag
        if self.X >= val:
            self.flags = set_bit(self.flags, 0, 1)
        else:
            self.flags = set_bit(self.flags, 0, 0)

        # If value of AX is equal to passed value, set zero flag
        if self.X == val:
            self.flags = set_bit(self.flags, 1, 1)
        else:
            self.flags = set_bit(self.flags, 1, 0)

        # If bit 7 of the result is set, set negative flag
        self.flags = set_bit(self.flags, 7, check_bit(result, 7))

    # Immediate
    def cpx_im(self, val):
        print("CPX #$" + hfmt(val))

        self.cpx(val)

        self.offset += 1

    # Zero Page
    def cpx_zp(self, addr):
        print("CPX $" + hfmt(addr))

        val = self.ram.read(addr)

        self.cpx(val)

        self.offset += 1

    """ - CPY - Compare Y Register """
    # Base
    def cpy(self, val):
        result = bsub(self.Y, val)[0]

        # If value of AX is greater than passed value, set carry flag
        if self.Y >= val:
            self.flags = set_bit(self.flags, 0, 1)
        else:
            self.flags = set_bit(self.flags, 0, 0)

        # If value of AX is equal to passed value, set zero flag
        if self.Y == val:
            self.flags = set_bit(self.flags, 1, 1)
        else:
            self.flags = set_bit(self.flags, 1, 0)

        # If bit 7 of the result is set, set negative flag
        self.flags = set_bit(self.flags, 7, check_bit(result, 7))

    # Immediate
    def cpy_im(self, val):
        print("CPY #$" + hfmt(val))

        self.cpy(val)

        self.offset += 1

    """ - JMP - Jump """
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

    """ - JSR - Jump to Subroutine """
    # Absolute
    def jsr_abs(self, addr):
        print("JSR $" + hfmt(addr, 4))

        # Push upper byte of program counter to stack
        self.ram.push(self.PC >> 8, self.SP - 1)
        # Push lower byte of program counter to stack
        self.ram.push((self.PC + 2) & 0xFF, self.SP)

        self.SP -= 2

        self.PC = addr - 1

    """ - RTS - Return from Subroutine """
    # Implied
    def rts(self):
        print("RTS")

        self.SP += 2
        self.PC = hcat(self.ram.pop(self.SP - 1), self.ram.pop(self.SP))

    """ - PHA - Push Accumulator """
    # Implied
    def pha(self):
        print("PHA")

        self.ram.push(self.AX, self.SP)
        self.SP -= 1

    """ - PLA - Pull Accumulator """
    # Implied
    def pla(self):
        print("PLA")

        self.SP += 1
        self.AX = self.ram.pop(self.SP)
