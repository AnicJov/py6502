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


def comp(val, size=8):

    val = list(bin_to_str(val).zfill(size))

    for i in range(0, size):
        if val[i] == '0':
            val[i] = '1'
        else:
            val[i] = '0'

    val = bin_to_str(int(''.join(val).zfill(size), 2) + 1)

    return int(val[:8])


def decomp(val):
    """ Takes in 1's complement binary number
        and returns its positive form """

    c = 1
    while val * 2 > c:
        val = val ^ c
        c = c << 1

    return val


def bin_to_str(val):
    return str(bin(val))[2:]


def str_to_bin(string):
    return int(string, 2)


def bsub(x, y, size=8):
    return badd(x, comp(y))


def badd(x, y, size=8):
        max_len = size

        x = bin_to_str(x).zfill(max_len)
        y = bin_to_str(y).zfill(max_len)

        result = ''
        carry = 0

        for i in range(max_len-1, -1, -1):
            r = carry
            r += 1 if x[i] == '1' else 0
            r += 1 if y[i] == '1' else 0
            result = ('1' if r % 2 == 1 else '0') + result
            carry = 0 if r < 2 else 1       

        if carry != 0:
            result = '1' + result

        return int(result.zfill(max_len)[:8], 2)
