from gym_driving.envs.xboxController import *
from gym_driving.envs.agents.driving_agent import *

import numpy as np

class Controller:
    def __init__(self, mode='keyboard', param_dict=None):
        """
        Initializes controller object to unify input interface.

        Args:
            mode: str, determines mode of input control.
                Must be in ['keyboard', 'xbox', 'agent'].
            param_dict: dict, parameters to pass into controller.
        """
        self.mode = mode
        if mode == 'keyboard':
            pass
        elif mode == 'xbox':
            self.xbox_controller = XboxController()
        elif mode == 'agent':
            self.agent = DrivingAgent(param_dict)
        else:
            raise NotImplementedError

    def process_input(self, env):
        """
        Process an input.

        Args:
            env: environment object, used for agent.

        Returns:
            action: 1x2 array, steer / acceleration action.
        """
        if self.mode == 'keyboard':
            action = self.process_keys()
        elif self.mode == 'xbox':
            action = self.process_xbox_controller()
        elif self.mode == 'agent':
            action = self.process_agent(env)
            # print("Action Taken", action)
        return action

    def process_keys(self):
        """
        Process an input from the keyboard.

        Returns:
            action: 1x2 array, steer / acceleration action.
        """
        action_dict = {'steer': 0.0, 'acc': 0.0}
        steer, acc = 1, 1
        pygame.event.pump()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            acc = 2
        elif keys[pygame.K_DOWN]:
            acc = 0
        if keys[pygame.K_LEFT]:
            steer = 0
        elif keys[pygame.K_RIGHT]:
            steer = 2
        action = np.array([steer, acc])
        return action

    def process_xbox_controller(self):
        """
        Process an input from the Xbox controller.

        Returns:
            action: 1x2 array, steer / acceleration action.
        """
        action_dict = {'steer': 0.0, 'acc': 0.0}
        left_stick_horizontal, left_stick_vertical, \
        right_stick_horizontal, right_stick_vertical = \
                        self.xbox_controller.getUpdates()
        steer = np.rint(right_stick_horizontal) + 1
        acc = -np.rint(left_stick_vertical) + 1
        action = np.array([steer, acc])
        return action

    def process_agent(self, env):
        """
        Process an input from the agent.

        Args: 
            env: environment object, used for agent.
        Returns:
            action: 1x2 array, steer / acceleration action.
        """
        steer = self.agent.eval_policy(env, None)
        acc = 0
        action = np.array([steer, acc])
        return action

    def reset(self):
        """
        Resets the controller, used for agent.
        """
        if self.mode == 'keyboard':
            pass
        elif self.mode == 'xbox':
            pass
        elif self.mode == 'agent':
            self.agent.reset()