# Small library of rgb colors written by Andrija Jovanovic
# Version: 2.3.0

# color_name = (RED, GREEN, BLUE)
#               \    0 - 255   /

# - Basic Colors -
white = (255, 255, 255)
black = (0, 0, 0)
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
cyan = (0, 240, 240)
brown = (80, 40, 40)
yellow = (255, 255, 0)
pink = (255, 0, 255)
purple = (128, 0, 255)
grey = (128, 128, 128)
orange = (255, 128, 0)

# - Basic Shades -
light_blue = (0, 128, 255)
light_grey = (192, 192, 192)
dark_green = (0, 128, 0)
dark_blue = (0, 0, 128)
dark_red = (128, 0, 0)


# - Functions -

def darken(color, amount=50):
    """ Makes a color darker by a variable amount """

    new_color = [0, 0, 0]
    for i in range(0, 3):
        if color[i] - amount > 0:
            new_color[i] = color[i] - amount
        else:
            new_color[i] = 0
    return tuple(new_color)


def lighten(color, amount=50):
    """ Makes a color lighter by a variable amount """

    new_color = [0, 0, 0]
    for i in range(0, 3):
        if color[i] + amount < 255:
            new_color[i] = color[i] + amount
        else:
            new_color[i] = 255
    return tuple(new_color)


def mix(colors):
    """
        Mixes a list of colors
        by taking the average of the rgb values
    """

    new_color = [0, 0, 0]
    color_sum = [0, 0, 0]
    for color in colors:
        for i in range(0, 3):
            color_sum[i] += color[i]
        for i in range(0, 3):
            try:
                new_color[i] = int(color_sum[i] / (len(colors)))
            except ZeroDivisionError:
                return tuple([0, 0, 0])
    return tuple(new_color)
