import os
import time


def bprint(num):
	print("{0:b}".format(num))


def bfmt(num, size=8):
	try:
		return format(num, 'b').zfill(size)
	except ValueError:
		return num


def hfmt(num, size=2):
	length = '0' + str(size) + 'x'
	return format(num, length)


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
