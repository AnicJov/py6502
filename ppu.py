

from colors import *
from threading import Thread
import random
import numpy as np
import sys
if sys.platform == "win32":
    import pygame
    from pygame.locals import *


class PPU(Thread):
    # PyGame template.

    def __init__(self, cpu, scale=10, intensity=16, title="MOS 6502"):
        Thread.__init__(self)

        self.FPS = None
        self.clock = None
        self.width = None
        self.height = None
        self.screen = None
        self.buffer = None
        self.title = title

        self.scale = scale
        self.intensity = intensity

        self.cpu = cpu

    def run(self):
        # Initialise PyGame.
        pygame.init()

        # Set up the clock. This will tick every frame and thus maintain a relatively constant framerate. Hopefully.
        self.FPS = 16.0
        self.clock = pygame.time.Clock()

        # Set the window name
        pygame.display.set_caption(self.title)

        # Set up the window.
        self.width, self.height = 320, 320
        self.screen = pygame.display.set_mode((self.width, self.height))

        # screen is the surface representing the window.
        # PyGame surfaces can be thought of as screen sections that you can draw onto.
        # You can also draw surfaces onto other surfaces, rotate surfaces, and transform surfaces.

        # Main game loop.
        dt = 1 / self.FPS  # dt is the time since last frame.
        while True:  # Loop forever!
            self.update(dt)  # You can update/draw here, I've just moved the code for neatness.
            self.draw()

            dt = self.clock.tick(self.FPS)

    def update(self, dt):
        """
        Update game. Called once per frame.
        dt is the amount of time passed since last frame.
        If you want to have constant apparent movement no matter your framerate,
        what you can do is something like

        x += v * dt

        and this will scale your velocity based on time. Extend as necessary."""

        # Go through events that are passed to the script by the window.
        for event in pygame.event.get():
            # We need to handle these events. Initially the only one you'll want to care
            # about is the QUIT event, because if you don't handle it, your game will crash
            # whenever someone tries to exit.
            if event.type == QUIT:
                pygame.quit()  # Opposite of pygame.init
                sys.exit()  # Not including this line crashes the script on Windows. Possibly
                # on other operating systems too, but I don't know for sure.
            # Handle other events as you wish.

        self.buffer = []

        for i in range(0, 32*32):
            self.buffer.append(self.cpu.ram.heap[0x0200+i])

    def draw(self):
        """
        Draw things to the window. Called once per frame.
        """
        self.screen.fill((0, 0, 0))  # Fill the screen with black.

        # Redraw screen here.
        buff = np.reshape(self.buffer, (-1, 32))

        for y, line in enumerate(buff):
            for x, val in enumerate(line):
                if val * self.intensity > 255:
                    val = 255
                pygame.draw.rect(self.screen,
                                 (val*self.intensity, val*self.intensity, val*self.intensity),
                                 Rect(x*self.scale, y*self.scale, self.scale, self.scale))

        # Flip the display so that the things we drew actually show up.
        pygame.display.flip()
