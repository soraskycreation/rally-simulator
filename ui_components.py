import pygame
import os

class Button:
    def __init__(self, rect, text="", font=None, image_path=None, hover_path=None, 
                 bg_color=(40, 130, 200), text_color=(255, 255, 255)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font or pygame.font.SysFont(None, 28)
        self.bg_color = bg_color
        self.text_color = text_color
        
        self.image = None
        self.hover_image = None
        
        # Load custom image if file exists
        if image_path and os.path.exists(image_path):
            raw_img = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(raw_img, (self.rect.width, self.rect.height))
            
        if hover_path and os.path.exists(hover_path):
            raw_img = pygame.image.load(hover_path).convert_alpha()
            self.hover_image = pygame.transform.scale(raw_img, (self.rect.width, self.rect.height))

    def is_hovered(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    def draw(self, surface, mouse_pos):
        hovered = self.is_hovered(mouse_pos)
        
        # 1. Render Image (if available)
        if hovered and self.hover_image:
            surface.blit(self.hover_image, self.rect)
        elif self.image:
            surface.blit(self.image, self.rect)
        else:
            # 2. Render Placeholder Fallback (if no image exists yet)
            color = tuple(min(255, c + 35) for c in self.bg_color) if hovered else self.bg_color
            border_col = (255, 220, 0) if hovered else (70, 75, 90)
            
            pygame.draw.rect(surface, color, self.rect, border_radius=8)
            pygame.draw.rect(surface, border_col, self.rect, 2, border_radius=8)

        # 3. Render Text Overlay
        if self.text:
            txt_surf = self.font.render(self.text, True, self.text_color)
            txt_rect = txt_surf.get_rect(center=self.rect.center)
            surface.blit(txt_surf, txt_rect)


class BackgroundManager:
    def __init__(self, image_path=None):
        self.bg_image = None
        if image_path and os.path.exists(image_path):
            self.bg_image = pygame.image.load(image_path).convert()

    def draw(self, surface):
        sw, sh = surface.get_size()
        
        if self.bg_image:
            scaled = pygame.transform.scale(self.bg_image, (sw, sh))
            surface.blit(scaled, (0, 0))
        else:
            # Placeholder Grid Pattern
            surface.fill((18, 18, 24))
            grid_size = 50
            for x in range(0, sw, grid_size):
                pygame.draw.line(surface, (25, 27, 36), (x, 0), (x, sh))
            for y in range(0, sh, grid_size):
                pygame.draw.line(surface, (25, 27, 36), (0, y), (sw, y))