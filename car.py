import pygame
import math

class Car:
    def __init__(self, x, y, sprite_surface=None):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.angle = 0.0  # Degrees (0 = Facing Right)
        
        # Physics Parameters (Arcade physics baseline)
        self.acceleration = 0.4
        self.max_speed = 10.0
        self.friction = 0.97
        self.turn_speed = 3.8
        
        # --- CAR SIZE & HITBOX CONFIGURATION ---
        self.scale_factor = 2  # Scale factor for visual representation
        self.width = 32   # Increased visual size (was 32)
        self.height = 16  # Increased visual size (was 16)
        self.width *= self.scale_factor
        self.height *= self.scale_factor

        
        # Hitbox padding factor (0.85 = 85% of visual size for generous collision detection)
        self.hitbox_scale = 0.85
        # ----------------------------------------

        self.is_alive = True
        self.fitness = 0.0
        
        # Load and scale sprite to visual dimensions
        if sprite_surface:
            if sprite_surface.get_width() > 32 or sprite_surface.get_height() > 16:
                cropped = sprite_surface.subsurface(pygame.Rect(0, 0, 32, 16))
            else:
                cropped = sprite_surface
            self.raw_sprite = pygame.transform.smoothscale(cropped, (self.width, self.height))
        else:
            self.raw_sprite = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.rect(self.raw_sprite, (0, 180, 255), (0, 0, self.width, self.height), border_radius=4)

        # Create base collision mask scaled down from the visual sprite
        hb_w = max(1, int(self.width * self.hitbox_scale))
        hb_h = max(1, int(self.height * self.hitbox_scale))
        hitbox_surface = pygame.transform.smoothscale(self.raw_sprite, (hb_w, hb_h))
        self.base_mask = pygame.mask.from_surface(hitbox_surface)
        
        self.current_mask = self.base_mask
        self.rect = self.raw_sprite.get_rect(center=(self.pos.x, self.pos.y))
        
        # Sensors (-60°, -30°, 0°, 30°, 60°)
        self.sensor_angles = [-60, -30, 0, 30, 60]
        self.sensor_distances = [1.0] * len(self.sensor_angles)
        self.sensor_points = []

    def update(self, inputs):
        if not self.is_alive:
            return

        throttle = inputs.get('throttle', 0.0)
        steer = inputs.get('steer', 0.0)

        # Steering (Only turns while moving)
        speed = self.vel.length()
        if speed > 0.1:
            self.angle += steer * self.turn_speed * (1 if throttle >= 0 else -1)

        # Acceleration & Drag
        forward_vec = pygame.Vector2(1, 0).rotate(self.angle)
        self.vel += forward_vec * (throttle * self.acceleration)
        self.vel *= self.friction

        if self.vel.length() > self.max_speed:
            self.vel.scale_to_length(self.max_speed)

        # Update Position
        self.pos += self.vel
        self.fitness += speed

        # Update Visual Rect
        rotated_surf = pygame.transform.rotate(self.raw_sprite, -self.angle)
        self.rect = rotated_surf.get_rect(center=(self.pos.x, self.pos.y))

        # Update Rotated Hitbox Mask
        hb_w = max(1, int(self.width * self.hitbox_scale))
        hb_h = max(1, int(self.height * self.hitbox_scale))
        scaled_sprite = pygame.transform.smoothscale(self.raw_sprite, (hb_w, hb_h))
        rotated_hitbox = pygame.transform.rotate(scaled_sprite, -self.angle)
        self.current_mask = pygame.mask.from_surface(rotated_hitbox)

    def check_track_collision(self, track_mask, offset_x=0, offset_y=0):
        """Checks pixel-perfect overlap between the smaller car mask and off-track mask."""
        # Align smaller mask center with the car's current center
        mask_rect = self.current_mask.get_rect(center=(self.pos.x, self.pos.y))
        mask_offset = (int(mask_rect.x - offset_x), int(mask_rect.y - offset_y))
        
        if track_mask.overlap(self.current_mask, mask_offset):
            self.is_alive = False
            self.vel = pygame.Vector2(0, 0)
            return True
        return False

    def cast_sensors(self, track_mask, offset_x=0, offset_y=0):
        """Casts distance raycasts from car center against the track mask."""
        self.sensor_points = []
        max_dist = 120.0
        
        for i, rel_angle in enumerate(self.sensor_angles):
            ray_angle = self.angle + rel_angle
            ray_dir = pygame.Vector2(1, 0).rotate(ray_angle)
            
            dist = max_dist
            hit_point = self.pos + ray_dir * max_dist
            
            for step in range(4, int(max_dist), 4):
                test_pos = self.pos + ray_dir * step
                mask_x = int(test_pos.x - offset_x)
                mask_y = int(test_pos.y - offset_y)
                
                if 0 <= mask_x < track_mask.get_size()[0] and 0 <= mask_y < track_mask.get_size()[1]:
                    if track_mask.get_at((mask_x, mask_y)):
                        dist = step
                        hit_point = test_pos
                        break
                else:
                    dist = step
                    hit_point = test_pos
                    break
                    
            self.sensor_distances[i] = dist / max_dist
            self.sensor_points.append((self.pos, hit_point))
            
        return self.sensor_distances

    def get_telemetry(self):
        """Returns state data dictionary ready to send to AI or HUD."""
        return {
            "pos": (self.pos.x, self.pos.y),
            "velocity": (self.vel.x, self.vel.y),
            "speed": self.vel.length(),
            "angle": self.angle % 360,
            "sensors": self.sensor_distances,
            "is_alive": self.is_alive,
            "fitness": self.fitness
        }

    def draw(self, screen, draw_sensors=True):
        if not self.is_alive:
            return

        rotated_surf = pygame.transform.rotate(self.raw_sprite, -self.angle)
        screen.blit(rotated_surf, self.rect.topleft)

        if draw_sensors:
            for start, end in self.sensor_points:
                pygame.draw.line(screen, (255, 60, 60), start, end, 1)
                pygame.draw.circle(screen, (255, 220, 0), (int(end.x), int(end.y)), 2)

    @staticmethod
    def get_player_inputs(keys):
        throttle = 0.0
        steer = 0.0
        if keys[pygame.K_UP] or keys[pygame.K_w]: throttle += 1.0
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: throttle -= 1.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: steer -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: steer += 1.0
        return {'throttle': throttle, 'steer': steer}