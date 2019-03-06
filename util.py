import os
import time
import math


def digit_count(num, base=10):
    if num > 0:
        return int(math.log(num, base) + 1)
    else:
        return 1

def bprint(num):
    """ Prints a binary number <num> """

    print("{0:b}".format(num))


def bfmt(num, size=8):
    """ Returns the printable string version of a binary number <num> that's length <size> """

    if num > 2**size:
        return format((num >> size) & (2**size - 1), 'b').zfill(size)
    try:
        return format(num, 'b').zfill(size)
    except ValueError:
        return num


def hfmt(num, size=0):
    """ Returns the printable string version of a hex number <num> that's length <size> """
    if size == 0:
        size = digit_count(num, 16) + digit_count(num, 16) % 2

    length = '0' + str(size) + 'x'
    return format(num, length)


def hcat(*nums):
    """ Concatenates hex values together and returns it as an integer """

    string = ''

    for num in nums:
        string += hfmt(num, 2)

    return int(string, 16)


def clear():
    """ Clears the default I/O stream """

    os.system('cls' if os.name == 'nt' else 'clear')


#      f-tion ref | freq. in Hz
def freq(function, frequency=1.0):
    """ Runs <function> at the given <frequency> """

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
    """ Creates specified <directory> if it doesn't already exist """

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


def comp(val, size=8):
    """ Returns the one's complement of a positive number """

    return (2**size) - 1 - val


def twos_comp(val, size=8):
    """ Returns the two's complement of a positive number """

    val, carry = badd(comp(val, size), 1, size)
    return val


def decomp(val):
    """ Returns the absolute value of a one's complement negative number """

    c = 1
    while val * 2 > c:
        val = val ^ c
        c = c << 1

    return val


def twos_decomp(val, size):
    """ Returns the absolute value of a two's complement negative number """

    val = bsub(val, 1, size)
    val = decomp(val)
    return val


def badd(*nums, size=8):
    """ Adds two binary integers of a bit length of <size> using two's complement """

    max_num = 2**size - 1
    result = 0

    for num in nums:
        result += num

    if result > max_num:
        return result & max_num, 1
    else:
        return result & max_num, 0


def bsub(x, y, size=8):
    """ Subtracts two binary integers of a bit length of <size> using two's complement """

    return badd(x, twos_comp(y), size)


def bin_to_str(val):
    """ Converts binary integer to string of 1s and 0s """

    return str(bin(val))[2:]


def str_to_bin(string):
    """ Converts string of 1s and 0s to binary integer """

    return int(string, 2)

def is_immediate(addr):
    if 0x0600 < addr < 0x0800:
        return True
    else:
        return False
