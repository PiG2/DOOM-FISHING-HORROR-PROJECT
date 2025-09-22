from settings import *
from pygame.math import Vector2 as vec2
import pygame as pg


class Player:
    def __init__(self, engine):
        self.engine = engine
        self.thing = engine.wad_data.things[0]
        self.pos = self.thing.pos
        self.angle = self.thing.angle
        self.DIAG_MOVE_CORR = 1 / math.sqrt(2)
        self.height = PLAYER_HEIGHT
        self.floor_height = 0
        self.z_vel = 0
        self.radius = 16
        self.linedefs = engine.wad_data.linedefs
        self.vertexes = engine.wad_data.vertexes

    def update(self):
        self.get_height()
        self.control()

    def get_height(self):
        # self.height = self.engine.bsp.get_sub_sector_height() + PLAYER_HEIGHT
        self.floor_height = self.engine.bsp.get_sub_sector_height()

        if self.height < self.floor_height + PLAYER_HEIGHT:
            self.height += 0.4 * (self.floor_height + PLAYER_HEIGHT - self.height)
            self.z_vel = 0
        else:
            self.z_vel -= 0.9
            self.height += max(-15.0, self.z_vel)

    def control(self):
        speed = PLAYER_SPEED * self.engine.dt
        rot_speed = PLAYER_ROT_SPEED * self.engine.dt

        key_state = pg.key.get_pressed()
        mouse_rel = pg.mouse.get_rel()
        self.angle -= mouse_rel[0] * MOUSE_SENSITIVITY

        inc = vec2(0)
        if key_state[pg.K_a]:
            inc += vec2(0, speed)
        if key_state[pg.K_d]:
            inc += vec2(0, -speed)
        if key_state[pg.K_w]:
            inc += vec2(speed, 0)
        if key_state[pg.K_s]:
            inc += vec2(-speed, 0)

        if inc.x and inc.y:
            inc *= self.DIAG_MOVE_CORR

        inc.rotate_ip(self.angle)

        new_pos = self.pos + inc
        if not self.check_collision(new_pos):
            self.pos = new_pos
        else:
            self.try_slide_movement(inc)

    def check_collision(self, new_pos):
        for linedef in self.linedefs:
            if (linedef.back_sidedef_id != 0xFFFF and # uh-huh
                not (linedef.flags & self.engine.wad_data.LINEDEF_FLAGS['BLOCKING'])): # yep
                continue
            
            v1 = self.vertexes[linedef.start_vertex_id]
            v2 = self.vertexes[linedef.end_vertex_id]

            if self.point_to_line_distance(new_pos, v1, v2) < self.radius:
                return True  

        return False

    def check_collision_with_margin(self, new_pos, margin=2):
        for linedef in self.linedefs:
            if (linedef.back_sidedef_id != 0xFFFF and 
                not (linedef.flags & self.engine.wad_data.LINEDEF_FLAGS['BLOCKING'])):
                continue
            
            v1 = self.vertexes[linedef.start_vertex_id]
            v2 = self.vertexes[linedef.end_vertex_id]

            if self.point_to_line_distance(new_pos, v1, v2) < self.radius + margin:
                return True  

        return False

    def point_to_line_distance(self, point, line_start, line_end):
        line_vec = vec2(line_end.x - line_start.x, line_end.y - line_start.y)
        line_length_sq = line_vec.length_squared()

        if line_length_sq == 0:
            return point.distance_to(vec2(line_start.x, line_start.y))

        point_vec = vec2(point.x - line_start.x, point.y - line_start.y)
        t = max(0, min(1, point_vec.dot(line_vec) / line_length_sq))
        closest_point = vec2(line_start.x, line_start.y) + t * line_vec

        return point.distance_to(closest_point)

    def try_slide_movement(self, movement):
        x_movement = vec2(movement.x, 0)
        x_pos = self.pos + x_movement
        if not self.check_collision(x_pos):
            self.pos = x_pos
            return
        
        y_movement = vec2(0, movement.y)
        y_pos = self.pos + y_movement
        if not self.check_collision(y_pos):
            self.pos = y_pos
            return

    # voodoo magic shit
    def check_sector_collision(self, new_pos):
        current_sector = self.engine.bsp.get_sub_sector(self.pos)
        target_sector = self.engine.bsp.get_sub_sector(new_pos)
        
        if target_sector:
            height_diff = target_sector.floor_height - current_sector.floor_height
            if height_diff > 24:  
                return True
        
        return False