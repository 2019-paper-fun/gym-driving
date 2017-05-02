import numpy as np
import pygame
import os
import IPython
from scipy.integrate import odeint

from gym_driving.envs.rectangle import Rectangle
from gym_driving.envs.car import Car

class DynamicCar(Car):
    """
    Car object.
    Dynamic bicycle model:
        http://www.me.berkeley.edu/~frborrel/pdfpub/IV_KinematicMPC_jason.pdf
    Cornering stiffness calculation:
        http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.46.28&rep=rep1&type=pdf
    Yaw inertia estimate:
        https://www.degruyter.com/downloadpdf/j/mecdc.2013.11.issue-1/mecdc-2013-0003/mecdc-2013-0003.pdf
    Friction coefficients:
        http://www.gipsa-lab.grenoble-inp.fr/~moustapha.doumiati/MED2010.pdf
    """
    def __init__(self, x, y, width=50, length=25, angle=0.0, vel=0.0, acc=0.0, max_vel=20.0, mass=100.0, screen=None, screen_size=0, texture='main', graphics_mode=False):
        super(DynamicCar, self).__init__(x, y, width, length, angle, vel, acc, max_vel, mass, screen, screen_size, texture, graphics_mode)
        self.mass = 1000.0
        self.l_f = self.l_r = width / 2.0
        self.dangle = self.a_f = self.dx_body = self.dy_body = 0.0
        self.count = 0
        self.friction = 0.9

    def step(self, action, info_dict=None):
        self.count += 1
        delta_f, a_f = action

        # Convert to radians 
        delta_f, rad_angle, rad_dangle = np.radians(delta_f), np.radians(self.angle), np.radians(self.dangle)

        # Friction coefficient
        if info_dict is None:
            mu = 0.9
        else:
            collisions = info_dict['terrain_collisions']
            if len(collisions) == 0:
                mu = 0.9
            else:
                mu = min([terrain.friction for terrain in collisions])

        # Differential equations
        ode_state = [self.x, self.y, self.dx_body, self.dy_body, rad_angle, rad_dangle]
        aux_state = (mu, delta_f, a_f)
        t = np.arange(0.0, 1.0, 0.1)
        delta_ode_state = odeint(self.integrator, ode_state, t, args=aux_state)
        x, y, dx_body, dy_body, rad_angle, rad_dangle = delta_ode_state[-1]

        # Update car 
        self.x, self.y, self.dx_body, self.dy_body, self.angle, self.dangle = \
            x, y, dx_body, dy_body, np.rad2deg(rad_angle), np.rad2deg(rad_dangle)
        self.body_vel = np.sqrt(self.dx_body ** 2 + self.dy_body ** 2)
        self.angle %= 360.0
        min_dangle = 15.0
        self.dangle = max(min(self.dangle, min_dangle), -min_dangle)
        self.corners = self.calculate_corners()

    def integrator(self, state, t, mu, delta_f, a_f):
        x, y, dx_body, dy_body, rad_angle, rad_dangle = state
        # Yaw Inertia
        I_z = 2510.15 * 25.0

        # Slip angles
        alpha_f = -delta_f
        alpha_r = 0.0

        # Tire cornering stiffness
        c_f_est = self.mass * (self.l_r / (self.l_f + self.l_r))
        c_f = c_r = mu * c_f_est

        # Cornering force
        F_cf = -c_f * alpha_f
        F_cr = -c_r * alpha_r

        # Differential equations
        ddx_body = rad_dangle * dy_body + a_f
        ddy_body = -rad_dangle * dx_body + (2 / self.mass) * (F_cf * np.cos(delta_f) + F_cr)
        
        # Clamp acceleration if above maximum velocity
        body_vel = np.sqrt((ddx_body + dx_body) ** 2 + (ddy_body + dy_body) ** 2)
        if body_vel > self.max_vel:
            a = ddx_body ** 2 + ddy_body ** 2
            b = 2 * (ddx_body * dx_body + ddy_body * dy_body)
            c = dx_body ** 2 + dy_body ** 2 - self.max_vel ** 2
            sqrt_term = b**2 - 4*a*c

            # Truncate if ratio is too small to avoid floating point error
            epsilon = 0.0001
            if sqrt_term < epsilon:
                ratio = 0.0
            else:
                ratios = (-b + np.sqrt(b**2 - 4*a*c)) / (2*a) , (-b - np.sqrt(b**2 - 4*a*c)) / (2*a) 
                ratio = max(ratios)
            ddx_body, ddy_body = ddx_body * ratio, ddy_body * ratio

        dangle = (2 / I_z) * (self.l_f * F_cf - self.l_r * F_cr)
        ddangle = 0.0
        # dangle = rad_dangle
        # ddangle = (2 / I_z) * (self.l_f * F_cf - self.l_r * F_cr)

        dx = dx_body * np.cos(rad_angle) - dy_body * np.sin(rad_angle)
        dy = dx_body * np.sin(rad_angle) + dy_body * np.sin(rad_angle)
        
        # Clamp velocity
        vel = np.sqrt(dx ** 2 + dy ** 2)
        if vel > self.max_vel:
            ratio = self.max_vel / vel
            dx, dy = dx * ratio, dy * ratio

        output = [dx, dy, ddx_body, ddy_body, dangle, ddangle]
        return output
