#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2018 Andrija Jovanovic
#
# +-----------------------------------------------------+
# |      A MOS Technology 6502 Processor Emulator       |
# |       written in python by Andrija Jovanovic        |
# |                                                     |
# | Version 1.0      Date: 6/3/2019       File: cpu.py  |
# +-----------------------------------------------------+

from util import *
from threading import Thread
from ram import RAM
from random import randint


class CPU(Thread):

    def __init__(self, mode=0, frequency=1, rom_path="ROM/test13.bin", ram=None, console=True):

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
        self.ram.dump_heap()

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
        self.lookup_table = [self.unk] * 0x100

        self.lookup_table[0xEA] = lambda: self.nop()

        self.lookup_table[0xA9] = lambda: self.lda(self.immediate())
        self.lookup_table[0xA5] = lambda: self.lda(self.zero_page())
        self.lookup_table[0xB5] = lambda: self.lda(self.zero_page_x())
        self.lookup_table[0xA1] = lambda: self.lda(self.indirect_x())
        self.lookup_table[0xB1] = lambda: self.lda(self.indirect_y())

        self.lookup_table[0xA2] = lambda: self.ldx(self.immediate())
        self.lookup_table[0xA6] = lambda: self.ldx(self.zero_page())

        self.lookup_table[0xA0] = lambda: self.ldy(self.immediate())

        self.lookup_table[0x4A] = lambda: self.lsr(self.accumulator())
        self.lookup_table[0x46] = lambda: self.lsr(self.zero_page())
        self.lookup_table[0x4E] = lambda: self.lsr(self.absolute())

        self.lookup_table[0xE9] = lambda: self.sbc(self.immediate())
        self.lookup_table[0xE5] = lambda: self.sbc(self.zero_page())
        self.lookup_table[0xED] = lambda: self.sbc(self.absolute())

        self.lookup_table[0x38] = lambda: self.sec()

        self.lookup_table[0x85] = lambda: self.sta(self.zero_page())
        self.lookup_table[0x95] = lambda: self.sta(self.zero_page_x())
        self.lookup_table[0x8D] = lambda: self.sta(self.absolute())
        self.lookup_table[0x99] = lambda: self.sta(self.absolute_y())
        self.lookup_table[0x81] = lambda: self.sta(self.indirect_x())
        self.lookup_table[0x91] = lambda: self.sta(self.indirect_y())

        self.lookup_table[0x8E] = lambda: self.stx(self.absolute())
        self.lookup_table[0x96] = lambda: self.stx(self.zero_page_y())

        self.lookup_table[0x8C] = lambda: self.sty(self.absolute())

        self.lookup_table[0xAA] = lambda: self.tax()
        self.lookup_table[0x8A] = lambda: self.txa()

        self.lookup_table[0xE6] = lambda: self.inc(self.zero_page())
        self.lookup_table[0xE8] = lambda: self.inx()
        self.lookup_table[0xC8] = lambda: self.iny()

        self.lookup_table[0xC6] = lambda: self.dec(self.zero_page())
        self.lookup_table[0xCE] = lambda: self.dec(self.absolute())
        self.lookup_table[0xCA] = lambda: self.dex()

        self.lookup_table[0x29] = lambda: self.land(self.immediate())

        self.lookup_table[0x69] = lambda: self.adc(self.immediate())
        self.lookup_table[0x65] = lambda: self.adc(self.zero_page())

        self.lookup_table[0x24] = lambda: self.bit(self.zero_page())
        self.lookup_table[0x2C] = lambda: self.bit(self.absolute())

        self.lookup_table[0x00] = lambda: self.brk()

        self.lookup_table[0x90] = lambda: self.bcc(self.relative())
        self.lookup_table[0xB0] = lambda: self.bcs(self.relative())
        self.lookup_table[0xF0] = lambda: self.beq(self.relative())
        self.lookup_table[0xD0] = lambda: self.bne(self.relative())
        self.lookup_table[0x10] = lambda: self.bpl(self.relative())

        self.lookup_table[0x18] = lambda: self.clc()

        self.lookup_table[0xC9] = lambda: self.cmp(self.immediate())
        self.lookup_table[0xC5] = lambda: self.cmp(self.zero_page())
        self.lookup_table[0xE0] = lambda: self.cpx(self.immediate())
        self.lookup_table[0xE4] = lambda: self.cpx(self.zero_page())
        self.lookup_table[0xC0] = lambda: self.cpy(self.immediate())

        self.lookup_table[0x4C] = lambda: self.jmp(self.absolute())
        self.lookup_table[0x6C] = lambda: self.jmp(self.indirect())
        self.lookup_table[0x20] = lambda: self.jsr(self.absolute())

        self.lookup_table[0x60] = lambda: self.rts()

        self.lookup_table[0x48] = lambda: self.pha()
        self.lookup_table[0x68] = lambda: self.pla()

    def decode_instruction(self, instruction):
        """ Looks up instruction in memory and calls the appropriate function """

        try:
            opcode = instruction[0]

            if self.console:
                print("Current instruction: $", end='')
                print(hfmt(opcode))

            self.lookup_table[opcode]()

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

        return self.PC + 1

    def zero_page(self):
        self.offset += 1

        return self.PC + 1

    def zero_page_x(self):
        rel_addr = self.ram.read(self.PC + 1)

        if rel_addr + self.X > 255:
            addr = rel_addr + self.X - 255
        else:
            addr = rel_addr + self.X

        self.offset += 1

        return addr

    def zero_page_y(self):
        rel_addr = self.ram.read(self.PC + 1)

        if rel_addr + self.Y > 255:
            addr = rel_addr + self.Y - 255
        else:
            addr = rel_addr + self.Y

        self.offset += 1

        return addr

    def relative(self):
        self.offset += 1

        return self.PC + 1

    def absolute(self):
        addr = hcat(self.ram.read(self.PC + 2), self.ram.read(self.PC + 1))

        self.offset += 2

        return addr

    def absolute_x(self):
        addr = hcat(self.ram.read(self.PC + 2), self.ram.read(self.PC + 1)) + self.X

        self.offset += 2

        return addr

    def absolute_y(self):
        addr = hcat(self.ram.read(self.PC + 2), self.ram.read(self.PC + 1)) + self.Y

        self.offset += 2

        return addr

    def indirect(self):
        addr = hcat(self.ram.read(self.PC + 2), self.ram.read(self.PC + 1))

        self.offset += 2

        return hcat(self.ram.read(addr), self.ram.read(addr + 1))

    def indirect_x(self):
        ind_addr = hcat(self.ram.read(self.PC + 2), self.ram.read(self.PC + 1))

        if ind_addr + self.X > 255:
            rel_addr = ind_addr + self.X - 255
        else:
            rel_addr = ind_addr + self.X

        addr = hcat(self.ram.read(rel_addr), self.ram.read(rel_addr + 1))

        self.offset += 1

        return addr

    def indirect_y(self):
        addr = hcat(self.ram.read(self.ram.read(self.PC + 2) + 1), self.ram.read(self.ram.read(self.PC + 1))) + self.Y

        self.offset += 1

        return addr

    """
    
        -- Instructions --
        
    """

    """ - UNK - Unknown Instruction """
    def unk(self, opcode=0xFF):
        print("UNK $" + hfmt(opcode))

        self.offset += 0

    """ - NOP - No Operation """
    def nop(self):
        print("NOP")

        self.offset += 0

    """ - LDA - Load Accumulator - """
    def lda(self, addr):
        if is_immediate(addr):
            print("LDA #$" + hfmt(self.ram.read(addr)))
        else:
            print("LDA $" + hfmt(addr))

        self.AX = self.ram.read(addr)

        # Set zero flag
        self.zero_check(self.AX)
        # Set negative flag
        self.negative_check(self.AX)

    """ - LDX - Load X Register """
    def ldx(self, addr):
        if is_immediate(addr):
            print("LDX #$" + hfmt(self.ram.read(addr)))
        else:
            print("LDX $" + hfmt(addr))

        self.X = self.ram.read(addr)
        # Set zero flag
        self.zero_check(self.X)
        # Set negative flag
        self.negative_check(self.X)

    """ - LDY - Load Y Register """
    def ldy(self, addr):
        if is_immediate(addr):
            print("LDY #$" + hfmt(self.ram.read(addr)))
        else:
            print("LDY $" + hfmt(addr))

        self.Y = self.ram.read(addr)
        # Set zero flag
        self.zero_check(self.Y)
        # Set negative flag
        self.negative_check(self.Y)

    """ - LSR - Logical Shift Right """
    def lsr(self, addr):
        # Accumulator
        if addr is None:
            print("LSR")

            self.flags = set_bit(self.flags, 0, check_bit(self.AX, 0))
            self.AX = self.AX >> 1

        # All other addressing modes
        else:
            print("LSR $" + hfmt(addr))

            val = self.ram.read(addr)

            self.flags = set_bit(self.flags, 0, check_bit(val, 0))
            self.ram.write(addr, val >> 1)

    """ - SBC - Subtract with Carry """
    def sbc(self, addr):
        if is_immediate(addr):
            print("SBC #$" + hfmt(self.ram.read(addr)))
        else:
            print("SBC $" + hfmt(addr))

        val = self.ram.read(addr)

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
    def sec(self):
        print("SEC")

        self.flags = set_bit(self.flags, 0, 1)

    """ - STA - Store Accumulator """
    def sta(self, addr):
        print("STA $" + hfmt(addr))

        self.ram.write(self.ram.read(addr), self.AX)

    """ - STX - Store X Register """
    def stx(self, addr):
        print("STX $" + hfmt(addr))

        self.ram.write(self.ram.read(addr), self.X)

    """ - STY - Store Y Register """
    def sty(self, addr):
        print("STY $" + hfmt(addr))

        self.ram.write(self.ram.read(addr), self.Y)

    """ - TAX - Transfer Accumulator to X """
    def tax(self):
        print("TAX")

        self.X = self.AX
        # Set zero flag
        self.zero_check(self.X)
        # Set negative flag
        self.negative_check(self.X)

    """ - TXA - Transfer X to Accumulator """
    def txa(self):
        print("TXA")

        self.AX = self.X

        # Set zero flag
        self.zero_check(self.AX)
        # Set negative flag
        self.negative_check(self.AX)

    """ - INC - Increment Memory """
    def inc(self, addr):
        val = self.ram.read(addr)

        self.ram.write(addr, badd(val, 1)[0])

        # Set zero flag
        self.zero_check(val)
        # Set negative flag
        self.negative_check(val)

    """ - INX - Increment X Register """
    def inx(self):
        print("INX")

        self.X = badd(self.X, 1)[0]

        # Set zero flag
        self.zero_check(self.X)
        # Set negative flag
        self.negative_check(self.X)

    """ - INY - Increment Y Register """
    def iny(self):
        print("INY")

        self.Y = badd(self.Y, 1)[0]

        # Set zero flag
        self.zero_check(self.Y)
        # Set negative flag
        self.negative_check(self.Y)

    """ - DEC - Decrement Memory """
    def dec(self, addr):
        print("DEC $" + hfmt(addr))

        val = self.ram.read(addr) - 1

        if val < 0:
            self.ram.write(addr, 255)
        else:
            self.ram.write(addr, val)

    """ - DEX - Decrement X Register """
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
    def land(self, addr):
        if is_immediate(addr):
            print("AND #$" + hfmt(self.ram.read(addr)))
        else:
            print("AND $" + hfmt(addr))

        val = self.ram.read(addr)

        self.AX = self.AX & val

        self.zero_check(self.AX)
        self.negative_check(self.AX)

    """ - ADC - Add with Carry """
    def adc(self, addr):
        if is_immediate(addr):
            print("ADC #$" + hfmt(self.ram.read(addr)))
        else:
            print("ADC $" + hfmt(addr))

        val = self.ram.read(addr)
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

    """ - BIT - Bit Test """
    # Zero Page
    def bit(self, addr):
        print("BIT $" + hfmt(addr))

        val = self.ram.read(addr)

        if self.AX & val == 0:
            self.flags = set_bit(self.flags, 1, 1)
        else:
            self.flags = set_bit(self.flags, 1, 0)

        self.flags = set_bit(self.flags, 6, check_bit(val, 6))
        self.flags = set_bit(self.flags, 7, check_bit(val, 7))

    """ - BRK - Force Interrupt """
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
                self.PC -= (num + 1)
            # If number is positive add it to the program counter
            else:
                self.PC += (addr + 1)

    """ - BCS - Branch if Carry Set """
    def bcs(self, addr):
        print("BCS $" + hfmt(addr))

        # If carry bit is set add relative displacement
        if check_bit(self.flags, 0):
            # If number is negative subtract it's two's complement
            if check_bit(addr, 7):
                num = decomp(addr)
                self.PC -= (num + 1)
            # If number is positive add it to the program counter
            else:
                self.PC += (addr + 1)

    """ - BEQ - Branch if Equal """
    def beq(self, addr):
        print("BEQ $" + hfmt(addr))

        # If zero bit is set add relative displacement
        if check_bit(self.flags, 1):
            # If number is negative subtract it's two's complement
            if check_bit(addr, 7):
                num = decomp(addr)
                self.PC -= (num + 1)
            # If number is positive add it to the program counter
            else:
                self.PC += (addr + 1)

    """ - BNE - Branch if Not Equal """
    def bne(self, addr):
        addr = self.ram.read(addr)

        print("BNE $" + hfmt(addr))

        # If zero bit is clear add relative displacement
        if not check_bit(self.flags, 1):
            # If number is negative subtract it's two's complement
            if check_bit(addr, 7):
                num = decomp(addr)
                self.PC -= (num + 1)
            # If number is positive add it to the program counter
            else:
                self.PC += (addr + 1)

    """ - BPL - Branch if Positive """
    def bpl(self, addr):
        print("BPL $" + hfmt(addr))

        # If negative bit is clear add relative displacement
        if not check_bit(self.flags, 7):
            # If number is negative subtract it's two's complement
            if check_bit(addr, 7):
                num = decomp(addr)
                self.PC -= (num + 1)
            # If number is positive add it to the program counter
            else:
                self.PC += (addr + 1)

    """ - CLC - Clear Carry Flag """
    def clc(self):
        print("CLC")

        self.flags = set_bit(self.flags, 0, 0)

    """ - CMP - Compare """
    def cmp(self, addr):
        if is_immediate(addr):
            print("CMP #$" + hfmt(self.ram.read(addr)))
        else:
            print("CMP $" + hfmt(addr))

        val = self.ram.read(addr)
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

    """ - CPX - Compare X Register """
    def cpx(self, addr):
        if is_immediate(addr):
            print("CPX #$" + hfmt(self.ram.read(addr)))
        else:
            print("CPX $" + hfmt(addr))

        val = self.ram.read(addr)

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

    """ - CPY - Compare Y Register """
    def cpy(self, addr):
        if is_immediate(addr):
            print("CPY #$" + hfmt(self.ram.read(addr)))
        else:
            print("CPY $" + hfmt(addr))

        val = self.ram.read(addr)

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

    """ - JMP - Jump """
    def jmp(self, addr):
        print("JMP $" + hfmt(addr))

        self.PC = addr - 1

        self.offset = 0

    """ - JSR - Jump to Subroutine """
    def jsr(self, addr):
        print("JSR $" + hfmt(addr))

        # Push upper byte of program counter to stack
        self.ram.push(self.PC >> 8, self.SP - 1)
        # Push lower byte of program counter to stack
        self.ram.push((self.PC + 2) & 0xFF, self.SP)

        self.SP -= 2

        self.PC = addr - 3

    """ - RTS - Return from Subroutine """
    def rts(self):
        print("RTS")

        self.SP += 2
        self.PC = hcat(self.ram.pop(self.SP - 1), self.ram.pop(self.SP))

    """ - PHA - Push Accumulator """
    def pha(self):
        print("PHA")

        self.ram.push(self.AX, self.SP)
        self.SP -= 1

    """ - PLA - Pull Accumulator """
    def pla(self):
        print("PLA")

        self.SP += 1
        self.AX = self.ram.pop(self.SP)
