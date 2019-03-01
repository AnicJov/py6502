from util import *
from threading import Thread


class RAM(Thread):

    def __init__(self, data_width=8, address_space=2**16):

        Thread.__init__(self)

        self.data_width = data_width
        self.address_space = address_space

        self.heap = []

        self.init_heap()

    def __repr__(self):
        stack = []
        for i in range(0, 4):
            try:
                stack.append(self.heap[0x01ff - i])
            except IndexError:
                stack.append("    /   ")
                continue

        heap = []
        for i in range(0, 4):
            try:
                heap.append(self.heap[i])
            except IndexError:
                heap.append("    /   ")
                continue

        state = "+=======================================+\n"\
                "| " + bfmt(stack[0]) + "  |  " + bfmt(stack[1]) + "   |  " + bfmt(stack[2]) + "   |\n"\
                "+=======================================+\n"\
                "|  Stack ↑        |RAM|        Heap ↓   |\n"\
                "+=======================================+\n"\
                "| " + bfmt(heap[0]) + "  |  " + bfmt(heap[1]) + "   |  " + bfmt(heap[2]) + "   |\n"\
                "+=======================================+\n"
        return state

    def init_heap(self):
        """ Populates the heap array with zero values up to the length <self.address_space> """

        for _ in range(0, self.address_space):
            self.heap.append(0b00000000)

    def push(self, data, sp):
        """ Writes <data> into address that <sp> is pointing to """

        self.heap[sp] = data

    def pop(self, sp):
        """ Returns the value at the address that <sp> is pointing to and sets it to zero """

        val = self.heap[sp]
        self.heap[sp] = 0b00000000
        return val

    def write(self, addr, data):
        """ Writes <data> in the heap at the specified address <addr> """

        self.heap[addr] = data

    def read(self, addr):
        """ Returns the value at the specified address <addr> """

        return self.heap[addr]

    def dump_heap(self):
        """ Creates a 'RAM' directory and writes a file 'heap.txt' with all of the memory addresses and contents """

        make_dir("RAM")
        with open("RAM/heap.txt", 'w', encoding="utf-8") as f:
            for addr, val in enumerate(self.heap):
                f.write("0x" + hfmt(addr, 4) + ": 0x" + hfmt(val) + " 0b" + bfmt(val) + "\n")


if __name__ == "__main__":
    ram = RAM()
    print(ram)
