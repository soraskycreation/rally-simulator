import pygame
import time

class LoadingScreen:
    def __init__(self, screen, target_action, slot_id=None, min_duration=2.0):
        self.screen = screen
        self.target_action = target_action  # "MENU", "EDIT", or "RACE"
        self.slot_id = slot_id
        self.min_duration = min_duration
        self.start_time = time.time()
        
        self.font_title = pygame.font.SysFont(None, 48)
        self.font_sub = pygame.font.SysFont(None, 24)
        self.progress = 0.0

    def handle_events(self, events):
        return None

    def update(self):
        elapsed = time.time() - self.start_time
        self.progress = min(1.0, elapsed / self.min_duration)
        
        if elapsed >= self.min_duration:
            return {
                "action": "LOADING_COMPLETE", 
                "target_action": self.target_action, 
                "slot_id": self.slot_id
            }
        return None

    def draw(self):
        sw, sh = self.screen.get_size()
        self.screen.fill((12, 12, 16))

        # Inside scenes/loading.py -> draw() method:
        if self.target_action == "STARTUP":
            lbl_str = "PIXEL RALLY SIMULATOR..."
            sub_str = "Loading engine & resources..."
        elif self.target_action == "EDIT":
            lbl_str = "LOADING TRACK EDITOR..."
            sub_str = f"Loading Slot {self.slot_id}..."
        else:
            lbl_str = "PREPARING RACE SIMULATION..."
            sub_str = f"Loading Slot {self.slot_id}..."

        title_txt = self.font_title.render(lbl_str, True, (255, 220, 0))
        self.screen.blit(title_txt, (sw // 2 - title_txt.get_width() // 2, sh // 2 - 60))

        sub_txt = self.font_sub.render(sub_str, True, (160, 160, 170))
        self.screen.blit(sub_txt, (sw // 2 - sub_txt.get_width() // 2, sh // 2 - 10))
        # Outer Progress Bar Frame
        bar_w, bar_h = 400, 22
        bar_rect = pygame.Rect(sw // 2 - bar_w // 2, sh // 2 + 30, bar_w, bar_h)
        pygame.draw.rect(self.screen, (32, 35, 45), bar_rect, border_radius=10)
        pygame.draw.rect(self.screen, (65, 70, 85), bar_rect, 2, border_radius=10)

        # Progress Fill
        fill_w = int((bar_w - 4) * self.progress)
        if fill_w > 0:
            fill_rect = pygame.Rect(bar_rect.x + 2, bar_rect.y + 2, fill_w, bar_h - 4)
            pygame.draw.rect(self.screen, (40, 170, 80), fill_rect, border_radius=8)