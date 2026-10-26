import pygame
from car import Car
from file_loader import load_slot
from spritesheet import Spritesheet

class RaceScene:
    def __init__(self, screen, slot_id="1"):
        self.screen = screen
        self.slot_id = str(slot_id)
        
        self.tile_size = 16
        self.scale = 4
        self.scaled_size = self.tile_size * self.scale
        self.cols, self.rows = 24, 14
        self.ui_height = 68
        
        self.sheet = Spritesheet('assets/rally_track.png')
        raw_grid, self.track_name = load_slot(self.slot_id, default_rows=self.rows, default_cols=self.cols)
        self.grid = raw_grid
        
        self.track_surface = self._render_track_surface()
        self.wall_mask = self._generate_wall_mask()
        self.finish_mask = self._generate_finish_mask()
        
        spawn_x, spawn_y, spawn_angle = self._find_spawn_point_and_angle()
        try:
            car_sprite = pygame.image.load('assets/rally_car.png').convert_alpha()
        except Exception:
            car_sprite = None
            
        self.car = Car(spawn_x, spawn_y, sprite_surface=car_sprite)
        self.car.angle = spawn_angle
        
        # Timer & Input-gate state
        self.timer_started = False
        self.start_time = 0
        self.finish_time = None
        self.finished = False
        
        self.back_btn = pygame.Rect(10, 12, 100, 44)
        self.reset_btn = pygame.Rect(120, 12, 90, 44)
        self.font = pygame.font.SysFont(None, 20)

    def _render_track_surface(self):
        surf = pygame.Surface((self.cols * self.scaled_size, self.rows * self.scaled_size), pygame.SRCALPHA)
        for r in range(self.rows):
            for c in range(self.cols):
                tile_info = self.grid[r][c]
                if tile_info:
                    if tile_info.get("is_start") or tile_info.get("is_finish"):
                        length = tile_info.get("length", 3)
                        gate_surf = pygame.Surface((self.tile_size * length, self.tile_size), pygame.SRCALPHA)
                        gate_surf.blit(self.sheet.get_tile(0, 15, scale=1), (0, 0))
                        mid_tile = self.sheet.get_tile(1, 15, scale=1)
                        for i in range(1, length - 1):
                            gate_surf.blit(mid_tile, (i * self.tile_size, 0))
                        gate_surf.blit(self.sheet.get_tile(2, 15, scale=1), ((length - 1) * self.tile_size, 0))
                        
                        gate_surf = pygame.transform.scale(gate_surf, (self.scaled_size * length, self.scaled_size))
                        if tile_info.get("angle", 0) != 0:
                            gate_surf = pygame.transform.rotate(gate_surf, -tile_info["angle"])
                        surf.blit(gate_surf, (c * self.scaled_size, r * self.scaled_size))
                    else:
                        tile_img = self.sheet.get_tile(tile_info["col"], tile_info["row"], scale=self.scale)
                        if tile_info.get("angle", 0) != 0:
                            tile_img = pygame.transform.rotate(tile_img, -tile_info["angle"])
                        surf.blit(tile_img, (c * self.scaled_size, r * self.scaled_size))
        return surf

    def _generate_wall_mask(self):
        wall_surf = pygame.Surface(self.track_surface.get_size(), pygame.SRCALPHA)
        px_array = pygame.PixelArray(self.track_surface)
        wall_array = pygame.PixelArray(wall_surf)
        
        w, h = self.track_surface.get_size()
        for y in range(h):
            for x in range(w):
                raw_color = px_array[x, y]
                color = self.track_surface.unmap_rgb(raw_color)
                
                if color.a < 50 or (color.g > color.r + 10 and color.g > color.b + 10):
                    wall_array[x, y] = (255, 255, 255, 255)
                    
        del px_array
        del wall_array
        return pygame.mask.from_surface(wall_surf)

    def _generate_finish_mask(self):
        finish_surf = pygame.Surface(self.track_surface.get_size(), pygame.SRCALPHA)
        for r in range(self.rows):
            for c in range(self.cols):
                tile = self.grid[r][c]
                if tile and tile.get("is_finish"):
                    length = tile.get("length", 3)
                    angle = tile.get("angle", 0)
                    gate_surf = pygame.Surface((self.tile_size * length, self.tile_size), pygame.SRCALPHA)
                    gate_surf.blit(self.sheet.get_tile(0, 15, scale=1), (0, 0))
                    mid_tile = self.sheet.get_tile(1, 15, scale=1)
                    for i in range(1, length - 1):
                        gate_surf.blit(mid_tile, (i * self.tile_size, 0))
                    gate_surf.blit(self.sheet.get_tile(2, 15, scale=1), ((length - 1) * self.tile_size, 0))
                    
                    gate_surf = pygame.transform.scale(gate_surf, (self.scaled_size * length, self.scaled_size))
                    if angle != 0:
                        gate_surf = pygame.transform.rotate(gate_surf, -angle)
                    finish_surf.blit(gate_surf, (c * self.scaled_size, r * self.scaled_size))
        return pygame.mask.from_surface(finish_surf)

    def _find_spawn_point_and_angle(self):
        offset_x, offset_y = self._get_canvas_offsets()
        for r in range(self.rows):
            for c in range(self.cols):
                tile = self.grid[r][c]
                if tile and tile.get("is_start"):
                    length = tile.get("length", 3)
                    angle = tile.get("angle", 0)
                    
                    if angle in (0, 180):
                        spawn_x = (c + length / 2.0) * self.scaled_size + offset_x
                        spawn_y = r * self.scaled_size + offset_y + (self.scaled_size // 2)
                    else:
                        spawn_x = c * self.scaled_size + offset_x + (self.scaled_size // 2)
                        spawn_y = (r + length / 2.0) * self.scaled_size + offset_y

                    spawn_angle = float(tile.get("facing_angle", 0.0))
                    return spawn_x, spawn_y, spawn_angle
                    
        return 100 + offset_x, 100 + offset_y, 0.0

    def _get_canvas_offsets(self):
        sw, sh = self.screen.get_size()
        grid_w = self.cols * self.scaled_size
        return max(0, (sw - grid_w) // 2), self.ui_height

    def handle_events(self, events):
        mx, my = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.back_btn.collidepoint(mx, my):
                    return {"action": "EDITOR", "slot_id": self.slot_id}
                elif self.reset_btn.collidepoint(mx, my):
                    self.reset_car()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return {"action": "EDITOR", "slot_id": self.slot_id}
                elif event.key == pygame.K_r:
                    self.reset_car()
        return None

    def reset_car(self):
        spawn_x, spawn_y, spawn_angle = self._find_spawn_point_and_angle()
        self.car.pos = pygame.Vector2(spawn_x, spawn_y)
        self.car.vel = pygame.Vector2(0, 0)
        self.car.angle = spawn_angle
        self.car.is_alive = True
        self.timer_started = False
        self.start_time = 0
        self.finish_time = None
        self.finished = False

    def update(self):
        offset_x, offset_y = self._get_canvas_offsets()
        
        keys = pygame.key.get_pressed()
        inputs = Car.get_player_inputs(keys)
        
        # Trigger timer on first user drive input
        if not self.timer_started and self.car.is_alive:
            if abs(inputs.get('throttle', 0.0)) > 0.0 or abs(inputs.get('steer', 0.0)) > 0.0:
                self.timer_started = True
                self.start_time = pygame.time.get_ticks()

        self.car.update(inputs)
        
        self.car.cast_sensors(self.wall_mask, offset_x=offset_x, offset_y=offset_y)
        self.car.check_track_collision(self.wall_mask, offset_x=offset_x, offset_y=offset_y)

        # Finish Line Detection
        if self.timer_started and not self.finished and self.car.is_alive:
            mask_offset = (int(self.car.rect.x - offset_x), int(self.car.rect.y - offset_y))
            if self.finish_mask.count() > 0 and self.finish_mask.overlap(self.car.current_mask, mask_offset):
                if pygame.time.get_ticks() - self.start_time > 1500:
                    self.finished = True
                    self.finish_time = pygame.time.get_ticks()

    def draw(self):
        sw, sh = self.screen.get_size()
        offset_x, offset_y = self._get_canvas_offsets()

        self.screen.fill((15, 15, 20))
        
        self.screen.blit(self.track_surface, (offset_x, offset_y))
        self.car.draw(self.screen, draw_sensors=True)
        
        pygame.draw.rect(self.screen, (25, 25, 30), (0, 0, sw, self.ui_height))
        pygame.draw.line(self.screen, (80, 80, 90), (0, self.ui_height), (sw, self.ui_height), 2)

        pygame.draw.rect(self.screen, (90, 40, 40), self.back_btn, border_radius=6)
        self.screen.blit(self.font.render("< EDITOR", True, (255, 255, 255)), (self.back_btn.x + 12, self.back_btn.y + 14))

        pygame.draw.rect(self.screen, (50, 50, 60), self.reset_btn, border_radius=6)
        self.screen.blit(self.font.render("RESET [R]", True, (255, 255, 255)), (self.reset_btn.x + 10, self.reset_btn.y + 14))

        # HUD Status & Timer display
        if not self.timer_started:
            status_txt = f"Track: {self.track_name} | Press WASD / Arrow Keys to Start"
            status_color = (255, 220, 0)
        elif self.finished:
            elapsed = (self.finish_time - self.start_time) / 1000.0
            status_txt = f"Track: {self.track_name} | FINISH! Time: {elapsed:.2f}s"
            status_color = (0, 255, 255)
        else:
            elapsed = (pygame.time.get_ticks() - self.start_time) / 1000.0
            spd = self.car.vel.length()
            status_color = (0, 255, 120) if self.car.is_alive else (255, 60, 60)
            status_txt = f"Track: {self.track_name} | Speed: {spd:.1f} | Time: {elapsed:.1f}s | Status: {'ALIVE' if self.car.is_alive else 'CRASHED'}"
            
        self.screen.blit(self.font.render(status_txt, True, status_color), (230, 26))