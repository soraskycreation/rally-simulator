import pygame

class Spritesheet:
    def __init__(self, filename):
        self.sheet = pygame.image.load(filename).convert_alpha()
    def get_tile(self, col, row, tile_size = 16, scale = 4):
        x = col * tile_size
        y = row * tile_size
        rect = pygame.Rect(x, y, tile_size, tile_size)
        image = self.sheet.subsurface(rect)
        if scale != 1:
            scaled_size = (tile_size * scale, tile_size * scale)
            image = pygame.transform.scale(image, scaled_size)

        return image

