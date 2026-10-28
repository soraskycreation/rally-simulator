import pygame
import math
from car import Car
from file_loader import load_slot, save_slot
from spritesheet import Spritesheet

class RaceScene:
    def __init__(self, screen, slot_id="1"):
        self.screen = screen
        self.slot_id = str(slot_id)
        
        self.tile_size = 16
        self.scale = 4
        self.scaled_size = self.tile_size * self.scale
        self.cols, self.rows = 24, 14
        self.ui_height = 80  # Increased slightly to fit two lines of HUD and buttons
        
        # Camera zoom factor
        self.zoom = 2.0
        
        self.sheet = Spritesheet('assets/rally_track.png')
        raw_grid, self.track_name, self.fastest_time = load_slot(self.slot_id, default_rows=self.rows, default_cols=self.cols)
        self.grid = raw_grid
        
        # Lap time history state
        self.previous_time = None
        
        self.track_surface = self._render_track_surface()
        self.wall_mask = self._generate_wall_mask()
        self.finish_mask = self._generate_finish_mask()
        
        # Radar Minimap Setup
        sw, sh = self.screen.get_size()
        minimap_w = 200
        minimap_h = int(self.track_surface.get_height() * (minimap_w / self.track_surface.get_width()))
        self.minimap_surf = pygame.transform.smoothscale(self.track_surface, (minimap_w, minimap_h))
        self.minimap_rect = pygame.Rect(sw - minimap_w - 20, self.ui_height + 20, minimap_w, minimap_h)
        self.minimap_scale_x = minimap_w / self.track_surface.get_width()
        self.minimap_scale_y = minimap_h / self.track_surface.get_height()
        
        spawn_x, spawn_y, spawn_angle = self._find_spawn_point_and_angle()
        try:
            car_sprite = pygame.image.load('assets/rally_car.png').convert_alpha()
        except Exception:
            car_sprite = None
            
        self.car = Car(spawn_x, spawn_y, sprite_surface=car_sprite)
        self.car.angle = spawn_angle
        
        self.camera_angle = self.car.angle
        
        # Timer & Input-gate state
        self.timer_started = False
        self.start_time = 0
        self.finish_time = None
        self.finished = False
        
        # UI Buttons
        self.back_btn = pygame.Rect(10, 10, 90, 30)
        self.reset_btn = pygame.Rect(110, 10, 90, 30)
        self.clear_best_btn = pygame.Rect(210, 10, 105, 30)
        self.restore_prev_btn = pygame.Rect(325, 10, 115, 30)
        
        self.font = pygame.font.SysFont(None, 18)

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
        for r in range(self.rows):
            for c in range(self.cols):
                tile = self.grid[r][c]
                if tile and tile.get("is_start"):
                    length = tile.get("length", 3)
                    angle = tile.get("angle", 0)
                    
                    if angle in (0, 180):
                        spawn_x = (c + length / 2.0) * self.scaled_size
                        spawn_y = r * self.scaled_size + (self.scaled_size // 2)
                    else:
                        spawn_x = c * self.scaled_size + (self.scaled_size // 2)
                        spawn_y = (r + length / 2.0) * self.scaled_size

                    spawn_angle = float(tile.get("facing_angle", 0.0))
                    return spawn_x, spawn_y, spawn_angle
                    
        return 100, 100, 0.0

    def handle_events(self, events):
        mx, my = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.back_btn.collidepoint(mx, my):
                    return {"action": "EDITOR", "slot_id": self.slot_id}
                elif self.reset_btn.collidepoint(mx, my):
                    self.reset_car()
                elif self.clear_best_btn.collidepoint(mx, my):
                    # Reset fastest time
                    self.fastest_time = None
                    save_slot(self.slot_id, self.grid, self.track_name, fastest_time=None)
                elif self.restore_prev_btn.collidepoint(mx, my):
                    # Restore previous run time as fastest time
                    if self.previous_time is not None:
                        self.fastest_time = self.previous_time
                        save_slot(self.slot_id, self.grid, self.track_name, fastest_time=self.fastest_time)
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
        self.camera_angle = spawn_angle
        self.car.is_alive = True
        self.timer_started = False
        self.start_time = 0
        self.finish_time = None
        self.finished = False

    def update(self):
        keys = pygame.key.get_pressed()
        inputs = Car.get_player_inputs(keys)
        
        if not self.timer_started and self.car.is_alive:
            if abs(inputs.get('throttle', 0.0)) > 0.0 or abs(inputs.get('steer', 0.0)) > 0.0:
                self.timer_started = True
                self.start_time = pygame.time.get_ticks()

        self.car.update(inputs)
        
        self.car.cast_sensors(self.wall_mask, offset_x=0, offset_y=0)
        self.car.check_track_collision(self.wall_mask, offset_x=0, offset_y=0)

        if self.timer_started and not self.finished and self.car.is_alive:
            mask_offset = (int(self.car.rect.x), int(self.car.rect.y))
            if self.finish_mask.count() > 0 and self.finish_mask.overlap(self.car.current_mask, mask_offset):
                if pygame.time.get_ticks() - self.start_time > 1500:
                    self.finished = True
                    self.finish_time = pygame.time.get_ticks()
                    
                    run_duration = (self.finish_time - self.start_time) / 1000.0
                    
                    # Update fastest and previous times
                    if self.fastest_time is None or run_duration < self.fastest_time:
                        self.previous_time = self.fastest_time
                        self.fastest_time = run_duration
                    else:
                        self.previous_time = run_duration
                        
                    save_slot(self.slot_id, self.grid, self.track_name, fastest_time=self.fastest_time)

    def draw(self):
        sw, sh = self.screen.get_size()
        screen_center = pygame.Vector2(sw // 2, sh // 2)

        # Smooth camera angle damping
        angle_diff = (self.car.angle - self.camera_angle + 180) % 360 - 180
        self.camera_angle += angle_diff * 0.12

        cam_rot = self.camera_angle + 90

        # Rotate track surface
        rotated_track = pygame.transform.rotate(self.track_surface, cam_rot)
        
        # Apply camera zoom to the track surface
        if self.zoom != 1.0:
            new_w = int(rotated_track.get_width() * self.zoom)
            new_h = int(rotated_track.get_height() * self.zoom)
            rotated_track = pygame.transform.smoothscale(rotated_track, (new_w, new_h))

        track_center_world = pygame.Vector2(self.track_surface.get_width() / 2, self.track_surface.get_height() / 2)
        car_offset_from_track = self.car.pos - track_center_world
        
        # Rotate and scale offset to match zoom
        rotated_offset = car_offset_from_track.rotate(-cam_rot) * self.zoom

        rotated_track_rect = rotated_track.get_rect()
        rotated_track_rect.center = (
            screen_center.x - rotated_offset.x,
            screen_center.y - rotated_offset.y
        )

        self.screen.fill((15, 15, 20))
        self.screen.blit(rotated_track, rotated_track_rect.topleft)

        # Draw zoomed car locked at screen center
        visual_angle_offset = (self.car.angle - self.camera_angle) * 0.3
        scaled_car_w = int(self.car.width * self.zoom)
        scaled_car_h = int(self.car.height * self.zoom)
        scaled_car_surf = pygame.transform.smoothscale(self.car.raw_sprite, (scaled_car_w, scaled_car_h))
        car_screen_surf = pygame.transform.rotate(scaled_car_surf, 90 + visual_angle_offset)
        car_rect = car_screen_surf.get_rect(center=(screen_center.x, screen_center.y))
        self.screen.blit(car_screen_surf, car_rect.topleft)

        # Draw sensor rays scaled with zoom
        for start, end in self.car.sensor_points:
            s_rel = start - self.car.pos
            e_rel = end - self.car.pos

            s_screen_rel = s_rel.rotate(-cam_rot) * self.zoom
            e_screen_rel = e_rel.rotate(-cam_rot) * self.zoom

            s_screen = (screen_center.x + s_screen_rel.x, screen_center.y + s_screen_rel.y)
            e_screen = (screen_center.x + e_screen_rel.x, screen_center.y + e_screen_rel.y)
            pygame.draw.line(self.screen, (255, 60, 60), s_screen, e_screen, 1)
            pygame.draw.circle(self.screen, (255, 220, 0), (int(e_screen[0]), int(e_screen[1])), 2)

        # UI Header Overlay
        pygame.draw.rect(self.screen, (25, 25, 30), (0, 0, sw, self.ui_height))
        pygame.draw.line(self.screen, (80, 80, 90), (0, self.ui_height), (sw, self.ui_height), 2)

        # Buttons
        pygame.draw.rect(self.screen, (90, 40, 40), self.back_btn, border_radius=4)
        self.screen.blit(self.font.render("< EDITOR", True, (255, 255, 255)), (self.back_btn.x + 8, self.back_btn.y + 7))

        pygame.draw.rect(self.screen, (50, 50, 60), self.reset_btn, border_radius=4)
        self.screen.blit(self.font.render("RESET [R]", True, (255, 255, 255)), (self.reset_btn.x + 8, self.reset_btn.y + 7))

        pygame.draw.rect(self.screen, (70, 40, 40), self.clear_best_btn, border_radius=4)
        self.screen.blit(self.font.render("RESET BEST", True, (255, 255, 255)), (self.clear_best_btn.x + 8, self.clear_best_btn.y + 7))

        pygame.draw.rect(self.screen, (40, 70, 70), self.restore_prev_btn, border_radius=4)
        self.screen.blit(self.font.render("RESTORE PREV", True, (255, 255, 255)), (self.restore_prev_btn.x + 6, self.restore_prev_btn.y + 7))

        # HUD Status Line
        best_str = f"{self.fastest_time:.2f}s" if self.fastest_time is not None else "None"
        prev_str = f"{self.previous_time:.2f}s" if self.previous_time is not None else "None"

        if not self.timer_started:
            status_txt = f"Track: {self.track_name} | Best: {best_str} | Prev: {prev_str} | Drive to Start"
            status_color = (255, 220, 0)
        elif self.finished:
            elapsed = (self.finish_time - self.start_time) / 1000.0
            status_txt = f"Track: {self.track_name} | FINISH! Time: {elapsed:.2f}s | Best: {best_str}"
            status_color = (0, 255, 255)
        else:
            elapsed = (pygame.time.get_ticks() - self.start_time) / 1000.0
            spd = self.car.vel.length()
            status_color = (0, 255, 120) if self.car.is_alive else (255, 60, 60)
            status_txt = f"Speed: {spd:.1f} | Current: {elapsed:.1f}s | Best: {best_str} | Prev: {prev_str} | {'ALIVE' if self.car.is_alive else 'CRASHED'}"
            
        self.screen.blit(self.font.render(status_txt, True, status_color), (15, 52))

        # Corner Radar Minimap UI
        pygame.draw.rect(self.screen, (25, 25, 35), self.minimap_rect.inflate(6, 6), border_radius=6)
        pygame.draw.rect(self.screen, (80, 80, 95), self.minimap_rect.inflate(6, 6), 2, border_radius=6)
        self.screen.blit(self.minimap_surf, self.minimap_rect.topleft)

        mini_car_x = self.minimap_rect.x + int(self.car.pos.x * self.minimap_scale_x)
        mini_car_y = self.minimap_rect.y + int(self.car.pos.y * self.minimap_scale_y)
        pygame.draw.circle(self.screen, (0, 220, 255), (mini_car_x, mini_car_y), 3)