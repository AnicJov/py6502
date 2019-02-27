import os
import time


def bprint(num):
    print("{0:b}".format(num))


def bfmt(num, size=8):
    if num > 2**size:
        return format((num >> size) & (2**size - 1), 'b').zfill(size)
    try:
        return format(num, 'b').zfill(size)
    except ValueError:
        return num


def hfmt(num, size=2):
    length = '0' + str(size) + 'x'
    return format(num, length)


def hcat(num1, num2):
    """ Concatenates two hex values """

    return int(hfmt(num1) + hfmt(num2), 16)


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


#      f-tion ref | freq. in Hz
def freq(function, frequency=1.0):
    while True:
        start = time.time()
        function()
        while True:
            current_time = time.time()
            try:
                if current_time - start >= 1.0/float(frequency):
                    break
            except ZeroDivisionError:
                break


def make_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def check_bit(val, n):
    """ Returns the value of the n-th (0 index) bit in given number """

    try:
        if val & 2**n:
            return 1
        else:
            return 0
    except TypeError:
        return -1


def set_bit(val, n, x=1):
    """ Returns val with the n-th (0 index) bit set to the value of x """

    mask = 1 << n
    val &= ~mask

    if x:
        val |= mask

    return val


def decomp(val):
    """ Takes in 1's complement binary number
        and returns its positive form """

    c = 1
    while val * 2 > c:
        val = val ^ c
        c = c << 1

    return val
