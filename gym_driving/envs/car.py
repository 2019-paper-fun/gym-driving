import numpy as np
import pygame
import os

from gym_driving.envs.rectangle import Rectangle


class Car(Rectangle):
    """
    Car object.
    """
    def __init__(self, x, y, width=50, length=25, angle=0.0, vel=0.0, acc=0.0, max_vel=20.0, mass=100.0, screen=None, screen_size=0, texture='main', graphics_mode=False):
        super(Car, self).__init__(x, y, width, length, angle)
        self.angle = angle
        self.vel_angle = angle
        self.vel = vel
        self.acc = acc
        self.max_vel = max_vel
        self.mass = mass
        self.screen = screen
        self.screen_size = screen_size
        self.texture = texture
        self.graphics_mode = graphics_mode

        car_textures = ['main', 'red', 'orange']
        if self.graphics_mode:
            if texture in car_textures:
                base_dir = os.path.dirname(__file__)
                filename = os.path.join(base_dir, 'images', '{}_car_lite.png'.format(texture))
                self.texture_image = pygame.image.load(filename)
            else:
                print('Error: invalid car texture')

    def step(self, t=1):
        """
        Updates car by one timestep.
        :param t: int
            Timestep.
        :return: None
        """
        dist = self.vel * t + 0.5 * self.acc * (t ** 2)
        dx = dist * np.cos(np.radians(self.vel_angle))
        dy = dist * np.sin(np.radians(self.vel_angle))
        self.x += dx
        self.y += dy
        self.vel += self.acc
        self.vel = max(min(self.vel, self.max_vel), 0.0)

    def take_action(self, action, terrain_collisions):
        """
        Updates car state according to action.
        :param action_dict: dict
            'steer': Change in steering angle.
            'acc': Acceleration.
        :return: None
        """
        # Get properties of terrain that the car is currently on
        decel = np.sum([t.decel for t in terrain_collisions])
        slip = np.sum([t.slip for t in terrain_collisions])

        # print('x,y', self.x, self.y)
        # print 'corners', self.get_corners()
        action_steer, action_acc = action 
        self.angle += action_steer
        self.angle %= 360.0
        if slip == 0:
            self.vel_angle = self.angle
        self.acc = action_acc - decel
        self.acc = max(min(self.acc, self.max_vel - self.vel), -self.vel)

    def get_state(self):
        state = np.array([self.x, self.y, self.angle])
        info_dict = {}
        info_dict['x'] = self.x
        info_dict['y'] = self.y
        info_dict['vel'] = self.vel
        info_dict['angle'] = self.angle
        info_dict['vel_angle'] = self.vel_angle
        return state, info_dict

    def update_graphics(self, screen_coord):
        assert self.graphics_mode is True
        corners, center, angle = self.get_corners(), self.get_pos(), self.angle
        x_offset = (np.abs((self.width - self.length) * np.cos(np.radians(angle))) + self.length) / 2
        y_offset = (np.abs((self.width - self.length) * np.sin(np.radians(angle))) + self.length) / 2
        # Subtract screen_coord to get screen pos
        image_rotated = pygame.transform.rotate(self.texture_image, -angle)
        if -100 <= center[0] - screen_coord[0] <= self.screen_size[0] and -100 <= center[1] - screen_coord[1] <= self.screen_size[1]:
            pos = (int(center[0] - screen_coord[0] - x_offset), int(center[1] - screen_coord[1] - y_offset))
            self.screen.blit(image_rotated, pos)