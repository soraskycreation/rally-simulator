import pygame
from file_loader import get_all_slots, create_new_slot
from ui_components import Button, BackgroundManager

class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.state = "MAIN"
        self.target_action = "EDIT"
        
        self.current_page = 0
        self.items_per_page = 3
        
        self.bg = BackgroundManager("assets/ui/bg_menu.png")
        
        self.font_title = pygame.font.SysFont(None, 64)
        self.font_btn = pygame.font.SysFont(None, 28)
        self.font_sub = pygame.font.SysFont(None, 22)

    def handle_events(self, events):
        sw, sh = self.screen.get_size()
        mx, my = pygame.mouse.get_pos()

        # Dynamic Main Menu Buttons
        btn_edit = Button((sw // 2 - 140, sh // 2 - 40, 280, 50), "TRACK EDITOR", 
                          font=self.font_btn, image_path="assets/ui/btn_edit.png", bg_color=(40, 130, 200))
        btn_race = Button((sw // 2 - 140, sh // 2 + 25, 280, 50), "RACE / SIMULATION", 
                          font=self.font_btn, image_path="assets/ui/btn_race.png", bg_color=(40, 170, 80))
        btn_settings = Button((sw // 2 - 140, sh // 2 + 90, 280, 50), "SETTINGS & CONTROLS", 
                              font=self.font_btn, image_path="assets/ui/btn_settings.png", bg_color=(100, 100, 110))
        btn_back = Button((40, 40, 110, 40), "< BACK", font=self.font_sub, bg_color=(100, 35, 35))

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == "MAIN":
                    if btn_edit.is_hovered((mx, my)):
                        self.target_action = "EDIT"
                        self.state = "SLOT_SELECT"
                    elif btn_race.is_hovered((mx, my)):
                        self.target_action = "RACE"
                        self.state = "SLOT_SELECT"
                    elif btn_settings.is_hovered((mx, my)):
                        self.state = "SETTINGS"

                elif self.state == "SLOT_SELECT":
                    if btn_back.is_hovered((mx, my)):
                        self.state = "MAIN"
                        return None

                    btn_new = Button((sw - 200, 40, 160, 40), "+ NEW TRACK", font=self.font_sub, bg_color=(35, 120, 60))
                    btn_prev = Button((sw // 2 - 130, sh - 70, 110, 40), "< PREV", font=self.font_sub, bg_color=(50, 55, 70))
                    btn_next = Button((sw // 2 + 20, sh - 70, 110, 40), "NEXT >", font=self.font_sub, bg_color=(50, 55, 70))

                    all_slots = get_all_slots()
                    slot_ids = sorted(list(all_slots.keys()), key=lambda x: int(x) if x.isdigit() else x)
                    total_pages = max(1, (len(slot_ids) + self.items_per_page - 1) // self.items_per_page)

                    if btn_new.is_hovered((mx, my)):
                        new_id = create_new_slot()
                        return {"action": "START_LOAD", "target_action": "EDIT", "slot_id": new_id}

                    if btn_prev.is_hovered((mx, my)) and self.current_page > 0:
                        self.current_page -= 1
                    elif btn_next.is_hovered((mx, my)) and self.current_page < total_pages - 1:
                        self.current_page += 1

                    # Card Clicking
                    start_idx = self.current_page * self.items_per_page
                    page_ids = slot_ids[start_idx : start_idx + self.items_per_page]

                    card_w, card_h = 230, 170
                    total_w = len(page_ids) * card_w + max(0, len(page_ids) - 1) * 25
                    start_x = (sw - total_w) // 2

                    for idx, s_id in enumerate(page_ids):
                        c_rect = pygame.Rect(start_x + idx * (card_w + 25), sh // 2 - 50, card_w, card_h)
                        if c_rect.collidepoint(mx, my):
                            return {"action": "START_LOAD", "target_action": self.target_action, "slot_id": s_id}

                elif self.state == "SETTINGS":
                    if btn_back.is_hovered((mx, my)):
                        self.state = "MAIN"
        return None

    def draw(self):
        sw, sh = self.screen.get_size()
        mx, my = pygame.mouse.get_pos()
        
        # Render Custom/Placeholder Background
        self.bg.draw(self.screen)

        if self.state == "MAIN":
            title_txt = self.font_title.render("PIXEL RALLY SIMULATOR", True, (255, 220, 0))
            self.screen.blit(title_txt, (sw // 2 - title_txt.get_width() // 2, sh // 5))

            btns = [
                Button((sw // 2 - 140, sh // 2 - 40, 280, 50), "TRACK EDITOR", 
                       font=self.font_btn, image_path="assets/ui/btn_edit.png", bg_color=(40, 130, 200)),
                Button((sw // 2 - 140, sh // 2 + 25, 280, 50), "RACE / SIMULATION", 
                       font=self.font_btn, image_path="assets/ui/btn_race.png", bg_color=(40, 170, 80)),
                Button((sw // 2 - 140, sh // 2 + 90, 280, 50), "SETTINGS & CONTROLS", 
                       font=self.font_btn, image_path="assets/ui/btn_settings.png", bg_color=(100, 100, 110))
            ]
            for btn in btns:
                btn.draw(self.screen, (mx, my))

        elif self.state == "SLOT_SELECT":
            header_str = "SELECT TRACK TO EDIT" if self.target_action == "EDIT" else "SELECT TRACK TO RACE"
            title_txt = self.font_title.render(header_str, True, (255, 255, 255))
            self.screen.blit(title_txt, (sw // 2 - title_txt.get_width() // 2, 45))

            Button((40, 40, 110, 40), "< BACK", font=self.font_sub, bg_color=(100, 35, 35)).draw(self.screen, (mx, my))
            Button((sw - 200, 40, 160, 40), "+ NEW TRACK", font=self.font_sub, bg_color=(35, 120, 60)).draw(self.screen, (mx, my))

            all_slots = get_all_slots()
            slot_ids = sorted(list(all_slots.keys()), key=lambda x: int(x) if x.isdigit() else x)
            total_pages = max(1, (len(slot_ids) + self.items_per_page - 1) // self.items_per_page)
            self.current_page = max(0, min(self.current_page, total_pages - 1))

            start_idx = self.current_page * self.items_per_page
            page_ids = slot_ids[start_idx : start_idx + self.items_per_page]

            card_w, card_h = 230, 170
            total_w = len(page_ids) * card_w + max(0, len(page_ids) - 1) * 25
            start_x = (sw - total_w) // 2

            for idx, s_id in enumerate(page_ids):
                c_rect = pygame.Rect(start_x + idx * (card_w + 25), sh // 2 - 50, card_w, card_h)
                slot_data = all_slots.get(s_id, {})
                track_name = slot_data.get("name", f"Track {s_id}")
                has_tiles = any(tile is not None for row in slot_data.get("grid", []) for tile in row)

                is_hover = c_rect.collidepoint(mx, my)
                card_color = (42, 48, 62) if is_hover else (28, 32, 42)
                border_color = (255, 220, 0) if is_hover else (65, 70, 85)

                pygame.draw.rect(self.screen, card_color, c_rect, border_radius=10)
                pygame.draw.rect(self.screen, border_color, c_rect, 3, border_radius=10)

                s_lbl = self.font_sub.render(f"SLOT {s_id}", True, (180, 180, 190))
                s_name = self.font_btn.render(track_name, True, (255, 255, 255))
                s_status = self.font_sub.render("Track Built" if has_tiles else "Empty Slot", True, 
                                                (100, 220, 120) if has_tiles else (130, 130, 140))

                self.screen.blit(s_lbl, (c_rect.centerx - s_lbl.get_width() // 2, c_rect.y + 20))
                self.screen.blit(s_name, (c_rect.centerx - s_name.get_width() // 2, c_rect.y + 60))
                self.screen.blit(s_status, (c_rect.centerx - s_status.get_width() // 2, c_rect.y + 115))

            if self.current_page > 0:
                Button((sw // 2 - 130, sh - 70, 110, 40), "< PREV", font=self.font_sub, bg_color=(50, 55, 70)).draw(self.screen, (mx, my))
            if self.current_page < total_pages - 1:
                Button((sw // 2 + 20, sh - 70, 110, 40), "NEXT >", font=self.font_sub, bg_color=(50, 55, 70)).draw(self.screen, (mx, my))

            page_indicator = self.font_sub.render(f"Page {self.current_page + 1} of {total_pages}", True, (160, 160, 170))
            self.screen.blit(page_indicator, (sw // 2 - page_indicator.get_width() // 2, sh - 100))

        elif self.state == "SETTINGS":
            title_txt = self.font_title.render("CONTROLS & KEYBINDS", True, (255, 255, 255))
            self.screen.blit(title_txt, (sw // 2 - title_txt.get_width() // 2, 70))

            Button((40, 40, 110, 40), "< BACK", font=self.font_sub, bg_color=(100, 35, 35)).draw(self.screen, (mx, my))

            keybinds = [
                ("Rotate Tile", "R Key"),
                ("Quick Palette Slots", "1 - 0 Keys"),
                ("Place Tile", "Left Click"),
                ("Erase Tile", "Right Click"),
                ("Steer Car (Racing)", "W / A / S / D or Arrow Keys"),
            ]

            panel_rect = pygame.Rect(sw // 2 - 250, 160, 500, 320)
            pygame.draw.rect(self.screen, (28, 32, 42), panel_rect, border_radius=10)
            pygame.draw.rect(self.screen, (65, 70, 85), panel_rect, 2, border_radius=10)

            for idx, (action, bind) in enumerate(keybinds):
                y_pos = 190 + idx * 50
                a_txt = self.font_btn.render(action, True, (200, 200, 210))
                b_txt = self.font_btn.render(bind, True, (255, 220, 0))
                self.screen.blit(a_txt, (panel_rect.x + 30, y_pos))
                self.screen.blit(b_txt, (panel_rect.right - 30 - b_txt.get_width(), y_pos))