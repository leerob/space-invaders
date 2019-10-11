import numpy as np

import pygame
from pygame.locals import *
from pygame import joystick

from utils.gamepad import *
from utils.navigation import MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT


class Input:
    """Handle input events"""

    def __init__(self):
        self.running = True
        pygame.init()
        pygame.joystick.init()
        self.num_joysticks = pygame.joystick.get_count()
        if self.num_joysticks > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

        self.gamepad_repeat_delay = 200
        self.gamepad_neutral = True
        self.gamepad_pressed_timer = 0
        self.gamepad_last_update = pygame.time.get_ticks()

    def handle_input(self, level, screen, scene):

        circuit_grid = level.circuit_grid

        # use joystick if it's connected
        if self.num_joysticks > 0:
            joystick_hat = joystick.get_hat(0)

            if joystick_hat == (0, 0):
                self.gamepad_neutral = True
                self.gamepad_pressed_timer = 0
            else:
                if self.gamepad_neutral:
                    gamepad_move = True
                    self.gamepad_neutral = False
                else:
                    self.gamepad_pressed_timer += pygame.time.get_ticks() - self.gamepad_last_update
            if self.gamepad_pressed_timer > self.gamepad_repeat_delay:
                gamepad_move = True
                self.gamepad_pressed_timer -= self.gamepad_repeat_delay
            if gamepad_move:
                if joystick_hat == (-1, 0):
                    self.move_update_circuit_grid_display(circuit_grid, MOVE_LEFT)
                elif joystick_hat == (1, 0):
                    self.move_update_circuit_grid_display(circuit_grid, MOVE_RIGHT)
                elif joystick_hat == (0, 1):
                    self.move_update_circuit_grid_display(circuit_grid, MOVE_UP)
                elif joystick_hat == (0, -1):
                    self.move_update_circuit_grid_display(circuit_grid, MOVE_DOWN)
            self.gamepad_last_update = pygame.time.get_ticks()

            # Check left thumbstick position
            left_thumb_x = joystick.get_axis(0)
            left_thumb_y = joystick.get_axis(1)

        # Handle Input Events
        for event in pygame.event.get():
            pygame.event.pump()

            if event.type == QUIT:
                self.running = False
            elif event.type == JOYBUTTONDOWN:
                if event.button == BTN_A:
                    # Place X gate
                    circuit_grid.handle_input_x()
                    circuit_grid.draw(screen)
                    self.update_paddle(level, screen, scene)
                    pygame.display.flip()
                elif event.button == BTN_X:
                    # Place Y gate
                    circuit_grid.handle_input_y()
                    circuit_grid.draw(screen)
                    self.update_paddle(level, screen, scene)
                    pygame.display.flip()
                elif event.button == BTN_B:
                    # Place Z gate
                    circuit_grid.handle_input_z()
                    circuit_grid.draw(screen)
                    self.update_paddle(level, screen, scene)
                    pygame.display.flip()
                elif event.button == BTN_Y:
                    # Place Hadamard gate
                    circuit_grid.handle_input_h()
                    circuit_grid.draw(screen)
                    self.update_paddle(level, screen, scene)
                    pygame.display.flip()
                elif event.button == BTN_RIGHT_TRIGGER:
                    # Delete gate
                    circuit_grid.handle_input_delete()
                    circuit_grid.draw(screen)
                    self.update_paddle(level, screen, scene)
                    pygame.display.flip()
                elif event.button == BTN_RIGHT_THUMB:
                    # Add or remove a control
                    circuit_grid.handle_input_ctrl()
                    circuit_grid.draw(screen)
                    self.update_paddle(level, screen, scene)
                    pygame.display.flip()
                elif event.button == BTN_LEFT_BUMPER:
                    # Update visualizations
                    # TODO: Refactor following code into methods, etc.
                    self.update_paddle(level, screen, scene)

            elif event.type == JOYAXISMOTION:
                # print("event: ", event)
                if event.axis == AXIS_RIGHT_THUMB_X and joystick.get_axis(AXIS_RIGHT_THUMB_X) >= 0.95:
                    circuit_grid.handle_input_rotate(np.pi / 8)
                    circuit_grid.draw(screen)
                    self.update_paddle(level, screen, scene)
                    pygame.display.flip()
                if event.axis == AXIS_RIGHT_THUMB_X and joystick.get_axis(AXIS_RIGHT_THUMB_X) <= -0.95:
                    circuit_grid.handle_input_rotate(-np.pi / 8)
                    circuit_grid.draw(screen)
                    self.update_paddle(level, screen, scene)
                    pygame.display.flip()
                if event.axis == AXIS_RIGHT_THUMB_Y and joystick.get_axis(AXIS_RIGHT_THUMB_Y) <= -0.95:
                    circuit_grid.handle_input_move_ctrl(MOVE_UP)
                    circuit_grid.draw(screen)
                    self.update_paddle(level, screen, scene)
                    pygame.display.flip()
                if event.axis == AXIS_RIGHT_THUMB_Y and joystick.get_axis(AXIS_RIGHT_THUMB_Y) >= 0.95:
                    circuit_grid.handle_input_move_ctrl(MOVE_DOWN)
                    circuit_grid.draw(screen)
                    self.update_paddle(level, screen, scene)
                    pygame.display.flip()

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                elif event.key == K_a:
                    circuit_grid.move_to_adjacent_node(MOVE_LEFT)
                    circuit_grid.draw(screen)
                    pygame.display.flip()
                elif event.key == K_d:
                    circuit_grid.move_to_adjacent_node(MOVE_RIGHT)
                    circuit_grid.draw(screen)
                    pygame.display.flip()
                elif event.key == K_w:
                    circuit_grid.move_to_adjacent_node(MOVE_UP)
                    circuit_grid.draw(screen)
                    pygame.display.flip()
                elif event.key == K_s:
                    circuit_grid.move_to_adjacent_node(MOVE_DOWN)
                    circuit_grid.draw(screen)
                    pygame.display.flip()
                elif event.key == K_x:
                    circuit_grid.handle_input_x()
                    circuit_grid.draw(screen)
                    self.update_paddle(level, screen, scene)
                    pygame.display.flip()
                elif event.key == K_y:
                    circuit_grid.handle_input_y()
                    circuit_grid.draw(screen)
                    self.update_paddle(level, screen, scene)
                    pygame.display.flip()
                elif event.key == K_z:
                    circuit_grid.handle_input_z()
                    circuit_grid.draw(screen)
                    self.update_paddle(level, screen, scene)
                    pygame.display.flip()
                elif event.key == K_h:
                    circuit_grid.handle_input_h()
                    circuit_grid.draw(screen)
                    self.update_paddle(level, screen, scene)
                    pygame.display.flip()
                elif event.key == K_SPACE:
                    circuit_grid.handle_input_delete()
                    circuit_grid.draw(screen)
                    self.update_paddle(level, screen, scene)
                    pygame.display.flip()
                elif event.key == K_c:
                    # Add or remove a control
                    circuit_grid.handle_input_ctrl()
                    circuit_grid.draw(screen)
                    self.update_paddle(level, screen, scene)
                    pygame.display.flip()
                elif event.key == K_UP:
                    # Move a control qubit up
                    circuit_grid.handle_input_move_ctrl(MOVE_UP)
                    circuit_grid.draw(screen)
                    self.update_paddle(level, screen, scene)
                    pygame.display.flip()
                elif event.key == K_DOWN:
                    # Move a control qubit down
                    circuit_grid.handle_input_move_ctrl(MOVE_DOWN)
                    circuit_grid.draw(screen)
                    self.update_paddle(level, screen, scene)
                    pygame.display.flip()
                elif event.key == K_LEFT:
                    # Rotate a gate
                    circuit_grid.handle_input_rotate(-np.pi / 8)
                    circuit_grid.draw(screen)
                    self.update_paddle(level, screen, scene)
                    pygame.display.flip()
                elif event.key == K_RIGHT:
                    # Rotate a gate
                    circuit_grid.handle_input_rotate(np.pi / 8)
                    circuit_grid.draw(screen)
                    self.update_paddle(level, screen, scene)
                    pygame.display.flip()
                elif event.key == K_TAB:
                    # Update visualizations
                    # TODO: Refactor following code into methods, etc.
                    self.update_paddle(level, screen, scene)

    def update_paddle(self, level, screen, scene):
        # Update visualizations
        # TODO: Refactor following code into methods, etc.

        circuit_grid_model = level.circuit_grid_model
        right_statevector = level.right_statevector
        circuit_grid = level.circuit_grid
        statevector_grid = level.statevector_grid

        circuit = circuit_grid_model.compute_circuit()
        statevector_grid.paddle_before_measurement(circuit, scene.qubit_num, 100)
        right_statevector.arrange()
        circuit_grid.draw(screen)
        pygame.display.flip()

    def move_update_circuit_grid_display(self, circuit_grid, direction):
        circuit_grid.move_to_adjacent_node(direction)
        circuit_grid.draw(screen)
        pygame.display.flip()
