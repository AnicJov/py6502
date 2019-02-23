from util import *
from threading import Thread


class RAM(Thread):

    def __init__(self, data_width=8, address_space=2**16):

        Thread.__init__(self)

        self.data_width = data_width
        self.address_space = address_space

        self.stack = []
        self.heap = []

        self.init_heap()

    def __repr__(self):
        stack = []
        for i in range(0, 4):
            try:
                stack.append(self.stack[i])
            except IndexError:
                stack.append("    /   ")
                continue

        state = "+=======================================+\n"\
                "| " + bfmt(stack[0]) + "  |  " + bfmt(stack[1]) + "   |  " + bfmt(stack[3]) + "   |\n"\
                "+=======================================+\n"\
                "|  Stack ↑        |RAM|        Heap ↓   |\n"\
                "+=======================================+\n"\
                "|                                       |\n"\
                "+=======================================+\n"
        return state

    def init_heap(self):
        for _ in range(0, self.address_space):
            self.heap.append(0b00000000)

    def push(self, data):
        self.stack.append(data)

    def pop(self):
        return self.stack.pop()

    def write(self, addr, data):
        self.heap[addr] = data

    def read(self, addr):
        return self.heap[addr]

    def dump_heap(self):
        make_dir("RAM")
        with open("RAM/heap.txt", 'w') as f:
            for addr in self.heap:
                f.write(bfmt(addr) + "\n")


if __name__ == "__main__":
    ram = RAM()
    print(ram)
