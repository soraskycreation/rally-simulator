import pygame
import copy
from spritesheet import Spritesheet
from file_loader import load_slot, save_slot

class TrackEditor:
    def __init__(self, screen, slot_id="1"):
        self.screen = screen
        self.slot_id = str(slot_id)
        
        self.tile_size = 16
        self.scale = 4
        self.scaled_size = self.tile_size * self.scale
        self.cols = 24
        self.rows = 14
        self.ui_height = 68
        
        self.banner_row = 15
        self.sheet = Spritesheet('assets/rally_track.png')
        
        raw_grid, self.track_name = load_slot(self.slot_id, default_rows=self.rows, default_cols=self.cols)
        self.grid = self._normalize_grid(raw_grid)
        
        self.original_grid = copy.deepcopy(self.grid)
        self.original_track_name = self.track_name
        self.undo_stack = []
        self.is_dirty = False
        self.pending_action = "NONE"
        self.pending_gate_pos = None
        self.selected_spawn_dir = 0.0  # Default facing right
        self.just_closed_modal = False
        
        self.dragging_gate = False
        self.gate_drag_start = None
        
        self.selected_tile = {"col": 0, "row": 0}
        self.selected_angle = 0
        self.editing_name = False
        
        self.palette_items = [
            (0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8), (0, 9),
            (0, 10), (0, 11), (0, 12), (0, 13), (0, 14), (0, self.banner_row), (0, 16), (1, 16), (2, 16), (3, 16)
        ]
        
        self.slot_size = 40
        self.slot_gap = 4
        self.slot_pitch = self.slot_size + self.slot_gap
        
        self.menu_btn = pygame.Rect(10, 12, 65, 44)
        self.save_btn = pygame.Rect(80, 12, 60, 44)
        self.sim_btn = pygame.Rect(145, 12, 85, 44)
        self.name_rect = pygame.Rect(235, 12, 140, 44)
        self.palette_start_x = 385
        
        self.font = pygame.font.SysFont(None, 20)
        self.badge_font = pygame.font.SysFont(None, 14, bold=True)
        self.modal_title_font = pygame.font.SysFont(None, 24, bold=True)
        self.modal_btn_font = pygame.font.SysFont(None, 16, bold=True)

    def push_undo_state(self):
        self.undo_stack.append(copy.deepcopy(self.grid))
        if len(self.undo_stack) > 30:
            self.undo_stack.pop(0)

    def undo(self):
        if self.undo_stack:
            self.grid = self.undo_stack.pop()
            self.check_dirty_status()

    def check_dirty_status(self):
        self.is_dirty = (self.grid != self.original_grid or self.track_name != self.original_track_name)

    def save_current_state(self):
        save_slot(self.slot_id, self.grid, self.track_name)
        self.original_grid = copy.deepcopy(self.grid)
        self.original_track_name = self.track_name
        self.is_dirty = False

    def _normalize_grid(self, grid):
        while len(grid) < self.rows:
            grid.append([None] * self.cols)
        for r in range(self.rows):
            while len(grid[r]) < self.cols:
                grid[r].append(None)
        return grid

    def _get_canvas_offsets(self):
        sw, sh = self.screen.get_size()
        grid_width = self.cols * self.scaled_size
        return max(0, (sw - grid_width) // 2), self.ui_height

    def is_finish_banner(self, tile_col, tile_row):
        return tile_row == self.banner_row and tile_col in [0, 1, 2]

    def get_banner_surface(self, scale=1, angle=0, length=3):
        surf = pygame.Surface((self.tile_size * length, self.tile_size), pygame.SRCALPHA)
        surf.blit(self.sheet.get_tile(0, self.banner_row, scale=1), (0, 0))
        mid_tile = self.sheet.get_tile(1, self.banner_row, scale=1)
        for i in range(1, length - 1):
            surf.blit(mid_tile, (i * self.tile_size, 0))
        surf.blit(self.sheet.get_tile(2, self.banner_row, scale=1), ((length - 1) * self.tile_size, 0))

        if scale != 1:
            surf = pygame.transform.scale(surf, (self.tile_size * length * scale, self.tile_size * scale))
        if angle != 0:
            surf = pygame.transform.rotate(surf, -angle)
        return surf

    def handle_events(self, events):
        sw, sh = self.screen.get_size()
        mx, my = pygame.mouse.get_pos()

        if self.pending_action in ("EXIT_MENU", "EXIT_RACE"):
            modal_rect = pygame.Rect(sw // 2 - 210, sh // 2 - 85, 420, 170)
            btn_save = pygame.Rect(modal_rect.x + 20, modal_rect.y + 105, 115, 38)
            btn_discard = pygame.Rect(modal_rect.x + 150, modal_rect.y + 105, 115, 38)
            btn_cancel = pygame.Rect(modal_rect.x + 280, modal_rect.y + 105, 115, 38)

            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    c_mx, c_my = event.pos
                    if btn_save.collidepoint(c_mx, c_my):
                        self.save_current_state()
                        target = "MENU" if self.pending_action == "EXIT_MENU" else "RACE"
                        return {"action": target, "slot_id": self.slot_id} if target == "RACE" else {"action": target}
                    elif btn_discard.collidepoint(c_mx, c_my):
                        self.grid = copy.deepcopy(self.original_grid)
                        self.track_name = self.original_track_name
                        self.is_dirty = False
                        target = "MENU" if self.pending_action == "EXIT_MENU" else "RACE"
                        return {"action": target, "slot_id": self.slot_id} if target == "RACE" else {"action": target}
                    elif btn_cancel.collidepoint(c_mx, c_my):
                        self.pending_action = "NONE"
            return None

        elif self.pending_action == "SELECT_GATE":
            modal_rect = pygame.Rect(sw // 2 - 190, sh // 2 - 120, 380, 240)
            btn_start = pygame.Rect(modal_rect.x + 20, modal_rect.y + 50, 165, 34)
            btn_finish = pygame.Rect(modal_rect.x + 195, modal_rect.y + 50, 165, 34)
            
            dirs = [("Right (0°)", 0.0), ("Down (90°)", 90.0), ("Left (180°)", 180.0), ("Up (270°)", 270.0)]
            dir_rects = []
            for i, (d_name, d_val) in enumerate(dirs):
                bx = modal_rect.x + 20 + (i % 2) * 175
                by = modal_rect.y + 118 + (i // 2) * 32
                dir_rects.append((pygame.Rect(bx, by, 165, 28), d_val))

            btn_confirm = pygame.Rect(modal_rect.x + 60, modal_rect.y + 188, 260, 34)

            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    c_mx, c_my = event.pos
                    if btn_start.collidepoint(c_mx, c_my):
                        self.temp_is_start = True
                    elif btn_finish.collidepoint(c_mx, c_my):
                        self.temp_is_start = False
                    elif btn_confirm.collidepoint(c_mx, c_my):
                        gc, gr = self.pending_gate_pos
                        is_start = getattr(self, 'temp_is_start', True)
                        
                        if is_start:
                            for r in range(self.rows):
                                for c in range(self.cols):
                                    if self.grid[r][c] and self.grid[r][c].get("is_start"):
                                        self.grid[r][c]["is_start"] = False

                        existing_tile = self.grid[gr][gc] or {}
                        length = existing_tile.get("length", 3)

                        self.grid[gr][gc] = {
                            "col": 0, "row": self.banner_row,
                            "angle": self.selected_angle,
                            "is_start": is_start,
                            "is_finish": not is_start,
                            "facing_angle": self.selected_spawn_dir,
                            "length": length
                        }
                        self.pending_action = "NONE"
                        self.just_closed_modal = True
                        self.check_dirty_status()
                    else:
                        for brect, d_val in dir_rects:
                            if brect.collidepoint(c_mx, c_my):
                                self.selected_spawn_dir = d_val
                                break
            return None

        hotkey_map = {
            pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3, pygame.K_5: 4,
            pygame.K_6: 5, pygame.K_7: 6, pygame.K_8: 7, pygame.K_9: 8, pygame.K_0: 9
        }

        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.editing_name:
                    if event.key == pygame.K_RETURN:
                        self.editing_name = False
                        self.check_dirty_status()
                    elif event.key == pygame.K_BACKSPACE:
                        self.track_name = self.track_name[:-1]
                        self.check_dirty_status()
                    elif len(self.track_name) < 14 and event.unicode.isprintable():
                        self.track_name += event.unicode
                        self.check_dirty_status()
                else:
                    if event.key == pygame.K_z and (event.mod & pygame.KMOD_CTRL):
                        self.undo()
                    elif event.key == pygame.K_r:
                        self.selected_angle = (self.selected_angle + 90) % 360
                    elif event.key in hotkey_map:
                        idx = hotkey_map[event.key]
                        if idx < len(self.palette_items):
                            p_col, p_row = self.palette_items[idx]
                            self.selected_tile["col"] = p_col
                            self.selected_tile["row"] = p_row
                            self.selected_angle = 0

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                offset_x, offset_y = self._get_canvas_offsets()

                if event.button == 1:
                    if my < self.ui_height:
                        self.editing_name = self.name_rect.collidepoint(mx, my)

                        if self.menu_btn.collidepoint(mx, my):
                            if self.is_dirty:
                                self.pending_action = "EXIT_MENU"
                            else:
                                return {"action": "MENU"}
                        elif self.save_btn.collidepoint(mx, my):
                            self.save_current_state()
                        elif self.sim_btn.collidepoint(mx, my):
                            if self.is_dirty:
                                self.pending_action = "EXIT_RACE"
                            else:
                                return {"action": "RACE", "slot_id": self.slot_id}
                        else:
                            slot_idx = (mx - self.palette_start_x) // self.slot_pitch
                            if 0 <= slot_idx < len(self.palette_items):
                                p_col, p_row = self.palette_items[slot_idx]
                                self.selected_tile["col"] = p_col
                                self.selected_tile["row"] = p_row
                                self.selected_angle = 0

                if my >= offset_y and not self.editing_name:
                    grid_col = (mx - offset_x) // self.scaled_size
                    grid_row = (my - offset_y) // self.scaled_size
                    if 0 <= grid_col < self.cols and 0 <= grid_row < self.rows:
                        tile = self.grid[grid_row][grid_col]
                        if tile and (tile.get("is_start") or tile.get("is_finish")):
                            # Check if holding left click to drag resize vs clicking to re-configure
                            if event.button == 1 and not pygame.key.get_mods() & pygame.KMOD_SHIFT:
                                # Open configuration popup for existing gate
                                self.pending_gate_pos = (grid_col, grid_row)
                                self.temp_is_start = tile.get("is_start", True)
                                self.selected_spawn_dir = tile.get("facing_angle", 0.0)
                                self.pending_action = "SELECT_GATE"
                            else:
                                self.dragging_gate = True
                                self.gate_drag_start = (grid_col, grid_row)
                        else:
                            if event.button == 1:
                                self.push_undo_state()

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.dragging_gate:
                    self.dragging_gate = False
                    self.check_dirty_status()

        return None

    def update(self):
        if self.editing_name or self.pending_action != "NONE":
            return

        mouse_buttons = pygame.mouse.get_pressed()
        
        if not mouse_buttons[0]:
            self.just_closed_modal = False

        if self.just_closed_modal:
            return

        mx, my = pygame.mouse.get_pos()
        offset_x, offset_y = self._get_canvas_offsets()

        if my >= offset_y:
            grid_col = (mx - offset_x) // self.scaled_size
            grid_row = (my - offset_y) // self.scaled_size

            if 0 <= grid_col < self.cols and 0 <= grid_row < self.rows:
                if self.dragging_gate and self.gate_drag_start:
                    start_c, start_r = self.gate_drag_start
                    tile = self.grid[start_r][start_c]
                    if tile:
                        new_len = max(3, abs(grid_col - start_c) + 1 if tile.get("angle", 0) in (0, 180) else abs(grid_row - start_r) + 1)
                        tile["length"] = new_len
                    return

                if mouse_buttons[0]:
                    sel_col = self.selected_tile["col"]
                    sel_row = self.selected_tile["row"]

                    if self.is_finish_banner(sel_col, sel_row):
                        self.pending_gate_pos = (grid_col, grid_row)
                        self.temp_is_start = True
                        self.selected_spawn_dir = 0.0
                        self.pending_action = "SELECT_GATE"
                    else:
                        self.grid[grid_row][grid_col] = {"col": sel_col, "row": sel_row, "angle": self.selected_angle}
                        self.check_dirty_status()

                elif mouse_buttons[2]:
                    self.grid[grid_row][grid_col] = None
                    self.check_dirty_status()

    def draw(self):
        sw, sh = self.screen.get_size()
        offset_x, offset_y = self._get_canvas_offsets()

        self.screen.fill((15, 15, 20))

        for r in range(self.rows):
            for c in range(self.cols):
                tile_info = self.grid[r][c]
                if tile_info:
                    if tile_info.get("is_start") or tile_info.get("is_finish"):
                        gate_surf = self.get_banner_surface(
                            scale=self.scale, 
                            angle=tile_info.get("angle", 0), 
                            length=tile_info.get("length", 3)
                        )
                        self.screen.blit(gate_surf, (c * self.scaled_size + offset_x, r * self.scaled_size + offset_y))
                    else:
                        tile_img = self.sheet.get_tile(tile_info["col"], tile_info["row"], scale=self.scale)
                        if tile_info.get("angle", 0) != 0:
                            tile_img = pygame.transform.rotate(tile_img, -tile_info["angle"])
                        self.screen.blit(tile_img, (c * self.scaled_size + offset_x, r * self.scaled_size + offset_y))

        grid_color = (40, 40, 40)
        max_w, max_h = self.cols * self.scaled_size + offset_x, self.rows * self.scaled_size + offset_y
        for c in range(self.cols + 1):
            pygame.draw.line(self.screen, grid_color, (c * self.scaled_size + offset_x, offset_y), (c * self.scaled_size + offset_x, max_h))
        for r in range(self.rows + 1):
            pygame.draw.line(self.screen, grid_color, (offset_x, r * self.scaled_size + offset_y), (max_w, r * self.scaled_size + offset_y))

        mx, my = pygame.mouse.get_pos()
        if my >= offset_y and not self.editing_name and self.pending_action == "NONE" and not self.just_closed_modal:
            grid_col = (mx - offset_x) // self.scaled_size
            grid_row = (my - offset_y) // self.scaled_size
            if 0 <= grid_col < self.cols and 0 <= grid_row < self.rows:
                sel_col, sel_row = self.selected_tile["col"], self.selected_tile["row"]
                if self.is_finish_banner(sel_col, sel_row):
                    ghost = self.get_banner_surface(scale=self.scale, angle=self.selected_angle, length=3)
                else:
                    ghost = self.sheet.get_tile(sel_col, sel_row, scale=self.scale)
                    if self.selected_angle != 0:
                        ghost = pygame.transform.rotate(ghost, -self.selected_angle)
                ghost.set_alpha(160)
                self.screen.blit(ghost, (grid_col * self.scaled_size + offset_x, grid_row * self.scaled_size + offset_y))

        pygame.draw.rect(self.screen, (25, 25, 30), (0, 0, sw, self.ui_height))
        pygame.draw.line(self.screen, (80, 80, 90), (0, self.ui_height), (sw, self.ui_height), 2)

        pygame.draw.rect(self.screen, (90, 40, 40), self.menu_btn, border_radius=6)
        self.screen.blit(self.font.render("< MENU", True, (255, 255, 255)), (self.menu_btn.x + 8, self.menu_btn.y + 14))

        pygame.draw.rect(self.screen, (40, 140, 50), self.save_btn, border_radius=6)
        self.screen.blit(self.font.render("SAVE", True, (255, 255, 255)), (self.save_btn.x + 12, self.save_btn.y + 14))

        pygame.draw.rect(self.screen, (40, 120, 180), self.sim_btn, border_radius=6)
        self.screen.blit(self.font.render("SIMULATE >", True, (255, 255, 255)), (self.sim_btn.x + 6, self.sim_btn.y + 14))

        name_bg = (55, 60, 75) if self.editing_name else (35, 38, 48)
        name_border = (255, 220, 0) if self.editing_name or self.is_dirty else (70, 75, 90)
        pygame.draw.rect(self.screen, name_bg, self.name_rect, border_radius=6)
        pygame.draw.rect(self.screen, name_border, self.name_rect, 2, border_radius=6)
        
        lbl_str = self.track_name + ("*" if self.is_dirty else "") + ("|" if self.editing_name else "")
        txt_surf = self.font.render(lbl_str, True, (255, 220, 0) if self.is_dirty else (255, 255, 255))
        self.screen.blit(txt_surf, (self.name_rect.x + 8, self.name_rect.y + 14))

        hotkey_labels = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
        for idx, (p_col, p_row) in enumerate(self.palette_items):
            px = self.palette_start_x + idx * self.slot_pitch
            py = 14
            pygame.draw.rect(self.screen, (45, 45, 50), (px, py, self.slot_size, self.slot_size), border_radius=4)

            if self.is_finish_banner(p_col, p_row):
                scaled_banner = pygame.transform.smoothscale(self.get_banner_surface(1, 0, 3), (36, 12))
                self.screen.blit(scaled_banner, (px + 2, py + 14))
            else:
                self.screen.blit(self.sheet.get_tile(p_col, p_row, scale=2.2), (px + 2, py + 2))

            if self.selected_tile["col"] == p_col and self.selected_tile["row"] == p_row:
                pygame.draw.rect(self.screen, (255, 220, 0), (px, py, self.slot_size, self.slot_size), 2, border_radius=4)

            if idx < len(hotkey_labels):
                badge = self.badge_font.render(hotkey_labels[idx], True, (255, 255, 255))
                pygame.draw.rect(self.screen, (0, 0, 0), (px + 2, py + 2, 11, 11), border_radius=2)
                self.screen.blit(badge, (px + 3, py + 1))

        self.screen.blit(self.font.render(f"Rot: {self.selected_angle}° [R]", True, (200, 200, 200)), (sw - 100, 26))

        if self.pending_action in ("EXIT_MENU", "EXIT_RACE"):
            overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))

            modal_rect = pygame.Rect(sw // 2 - 210, sh // 2 - 85, 420, 170)
            pygame.draw.rect(self.screen, (28, 30, 38), modal_rect, border_radius=10)
            pygame.draw.rect(self.screen, (255, 220, 0), modal_rect, 2, border_radius=10)

            title_surf = self.modal_title_font.render("UNSAVED CHANGES", True, (255, 220, 0))
            sub_surf = self.font.render("Save your changes before leaving?", True, (200, 200, 210))

            self.screen.blit(title_surf, (modal_rect.centerx - title_surf.get_width() // 2, modal_rect.y + 25))
            self.screen.blit(sub_surf, (modal_rect.centerx - sub_surf.get_width() // 2, modal_rect.y + 60))

            btn_save = pygame.Rect(modal_rect.x + 20, modal_rect.y + 105, 115, 38)
            btn_discard = pygame.Rect(modal_rect.x + 150, modal_rect.y + 105, 115, 38)
            btn_cancel = pygame.Rect(modal_rect.x + 280, modal_rect.y + 105, 115, 38)

            pygame.draw.rect(self.screen, (35, 120, 60), btn_save, border_radius=6)
            pygame.draw.rect(self.screen, (150, 40, 40), btn_discard, border_radius=6)
            pygame.draw.rect(self.screen, (70, 75, 85), btn_cancel, border_radius=6)

            self.screen.blit(self.modal_btn_font.render("SAVE & EXIT", True, (255, 255, 255)), (btn_save.x + 12, btn_save.y + 12))
            self.screen.blit(self.modal_btn_font.render("DISCARD", True, (255, 255, 255)), (btn_discard.x + 25, btn_discard.y + 12))
            self.screen.blit(self.modal_btn_font.render("CANCEL", True, (255, 255, 255)), (btn_cancel.x + 28, btn_cancel.y + 12))

        elif self.pending_action == "SELECT_GATE":
            overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))

            modal_rect = pygame.Rect(sw // 2 - 190, sh // 2 - 120, 380, 240)
            pygame.draw.rect(self.screen, (28, 30, 38), modal_rect, border_radius=10)
            pygame.draw.rect(self.screen, (0, 180, 255), modal_rect, 2, border_radius=10)

            title_surf = self.modal_title_font.render("CONFIGURE GATE", True, (0, 180, 255))
            self.screen.blit(title_surf, (modal_rect.centerx - title_surf.get_width() // 2, modal_rect.y + 15))

            btn_start = pygame.Rect(modal_rect.x + 20, modal_rect.y + 50, 165, 34)
            btn_finish = pygame.Rect(modal_rect.x + 195, modal_rect.y + 50, 165, 34)

            is_start_selected = getattr(self, 'temp_is_start', True)
            pygame.draw.rect(self.screen, (40, 140, 50) if is_start_selected else (50, 50, 60), btn_start, border_radius=6)
            pygame.draw.rect(self.screen, (180, 120, 30) if not is_start_selected else (50, 50, 60), btn_finish, border_radius=6)

            self.screen.blit(self.modal_btn_font.render("START GATE", True, (255, 255, 255)), (btn_start.x + 38, btn_start.y + 9))
            self.screen.blit(self.modal_btn_font.render("FINISH GATE", True, (255, 255, 255)), (btn_finish.x + 35, btn_finish.y + 9))

            lbl_dir = self.font.render("Car Facing Direction:", True, (200, 200, 210))
            self.screen.blit(lbl_dir, (modal_rect.x + 20, modal_rect.y + 92))

            dirs = [("Right (0°)", 0.0), ("Down (90°)", 90.0), ("Left (180°)", 180.0), ("Up (270°)", 270.0)]
            for i, (d_name, d_val) in enumerate(dirs):
                bx = modal_rect.x + 20 + (i % 2) * 175
                by = modal_rect.y + 118 + (i // 2) * 32
                brect = pygame.Rect(bx, by, 165, 28)
                is_active = (self.selected_spawn_dir == d_val)
                pygame.draw.rect(self.screen, (0, 120, 200) if is_active else (50, 55, 65), brect, border_radius=4)
                txt = self.modal_btn_font.render(d_name, True, (255, 255, 255))
                self.screen.blit(txt, (brect.centerx - txt.get_width() // 2, brect.centery - txt.get_height() // 2))

            btn_confirm = pygame.Rect(modal_rect.x + 60, modal_rect.y + 188, 260, 34)
            pygame.draw.rect(self.screen, (40, 160, 90), btn_confirm, border_radius=6)
            txt_conf = self.modal_btn_font.render("CONFIRM GATE", True, (255, 255, 255))
            self.screen.blit(txt_conf, (btn_confirm.centerx - txt_conf.get_width() // 2, btn_confirm.centery - txt_conf.get_height() // 2))