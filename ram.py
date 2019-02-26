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
        for _ in range(0, self.address_space):
            self.heap.append(0b00000000)

    def push(self, data, sp):
        self.heap[sp] = data

    def pop(self, sp):
        return self.heap[sp]

    def write(self, addr, data):
        self.heap[addr] = data

    def read(self, addr):
        return self.heap[addr]

    def dump_heap(self):
        make_dir("RAM")
        with open("RAM/heap.txt", 'w') as f:
            for addr, val in enumerate(self.heap):
                f.write("$" + hfmt(addr, 4) + ": " + bfmt(val) + "\n")


if __name__ == "__main__":
    ram = RAM()
    print(ram)
