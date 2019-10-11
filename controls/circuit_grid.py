#!/usr/bin/env python
#
# Copyright 2019 the original author or authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import numpy as np

import pygame

from model import circuit_node_types as node_types
from model.circuit_grid_model import CircuitGridNode
from utils.colors import BLACK, WHITE, MAGENTA
from utils.navigation import MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT
from utils.resources import load_image
from utils.parameters import WIDTH_UNIT, LINE_WIDTH, GRID_HEIGHT, GRID_WIDTH, GATE_TILE_WIDTH, GATE_TILE_HEIGHT


class CircuitGrid(pygame.sprite.RenderPlain):
    """Enables interaction with circuit"""

    def __init__(self, xpos, ypos, circuit_grid_model):
        self.xpos = xpos
        self.ypos = ypos
        self.circuit_grid_model = circuit_grid_model
        self.selected_wire = 0
        self.selected_column = 0
        self.circuit_grid_background = CircuitGridBackground(circuit_grid_model)
        self.circuit_grid_cursor = CircuitGridCursor()
        self.gate_tiles = np.empty((circuit_grid_model.max_wires, circuit_grid_model.max_columns),
                                   dtype=CircuitGridGate)

        for row_idx in range(self.circuit_grid_model.max_wires):
            for col_idx in range(self.circuit_grid_model.max_columns):
                self.gate_tiles[row_idx][col_idx] = \
                    CircuitGridGate(circuit_grid_model, row_idx, col_idx)

        pygame.sprite.RenderPlain.__init__(self, self.circuit_grid_background,
                                           self.gate_tiles,
                                           self.circuit_grid_cursor)
        self.update()

    def update(self, *args):

        sprite_list = self.sprites()
        for sprite in sprite_list:
            sprite.update()

        self.circuit_grid_background.rect.left = self.xpos
        self.circuit_grid_background.rect.top = self.ypos

        for row_idx in range(self.circuit_grid_model.max_wires):
            for col_idx in range(self.circuit_grid_model.max_columns):
                self.gate_tiles[row_idx][col_idx].rect.centerx = \
                    self.xpos + GRID_WIDTH * (col_idx + 1.5)
                self.gate_tiles[row_idx][col_idx].rect.centery = \
                    self.ypos + GRID_HEIGHT * (row_idx + 1.0)

        self.highlight_selected_node(self.selected_wire, self.selected_column)

    def highlight_selected_node(self, wire_num, column_num):
        self.selected_wire = wire_num
        self.selected_column = column_num
        self.circuit_grid_cursor.rect.left = self.xpos + GRID_WIDTH * (self.selected_column + 1) + round(
            0.375 * WIDTH_UNIT)
        self.circuit_grid_cursor.rect.top = self.ypos + GRID_HEIGHT * (self.selected_wire + 0.5) + round(
            0.375 * WIDTH_UNIT)

    def reset_cursor(self):
        self.highlight_selected_node(0, 0)

    def display_exceptional_condition(self):
        # TODO: Make cursor appearance indicate condition such as unable to place a gate
        return

    def move_to_adjacent_node(self, direction):
        if direction == MOVE_LEFT and self.selected_column > 0:
            self.selected_column -= 1
        elif direction == MOVE_RIGHT and self.selected_column < self.circuit_grid_model.max_columns - 1:
            self.selected_column += 1
        elif direction == MOVE_UP and self.selected_wire > 0:
            self.selected_wire -= 1
        elif direction == MOVE_DOWN and self.selected_wire < self.circuit_grid_model.max_wires - 1:
            self.selected_wire += 1

        self.highlight_selected_node(self.selected_wire, self.selected_column)

    def get_selected_node_gate_part(self):
        return self.circuit_grid_model.get_node_gate_part(self.selected_wire, self.selected_column)

    def handle_input_x(self):
        # Add X gate regardless of whether there is an existing gate
        # circuit_grid_node = CircuitGridNode(node_types.X)
        # self.circuit_grid_model.set_node(self.selected_wire, self.selected_column, circuit_grid_node)

        # Allow deleting using the same key only
        selected_node_gate_part = self.get_selected_node_gate_part()
        if selected_node_gate_part == node_types.EMPTY:
            circuit_grid_node = CircuitGridNode(node_types.X)
            self.circuit_grid_model.set_node(self.selected_wire, self.selected_column, circuit_grid_node)
        elif selected_node_gate_part == node_types.X:
            self.handle_input_delete()
        self.update()

    def handle_input_y(self):
        selected_node_gate_part = self.get_selected_node_gate_part()
        if selected_node_gate_part == node_types.EMPTY:
            circuit_grid_node = CircuitGridNode(node_types.Y)
            self.circuit_grid_model.set_node(self.selected_wire, self.selected_column, circuit_grid_node)
        elif selected_node_gate_part == node_types.Y:
            self.handle_input_delete()
        self.update()

    def handle_input_z(self):
        selected_node_gate_part = self.get_selected_node_gate_part()
        if selected_node_gate_part == node_types.EMPTY:
            circuit_grid_node = CircuitGridNode(node_types.Z)
            self.circuit_grid_model.set_node(self.selected_wire, self.selected_column, circuit_grid_node)
        elif selected_node_gate_part == node_types.Z:
            self.handle_input_delete()
        self.update()

    def handle_input_h(self):
        selected_node_gate_part = self.get_selected_node_gate_part()
        if selected_node_gate_part == node_types.EMPTY:
            circuit_grid_node = CircuitGridNode(node_types.H)
            self.circuit_grid_model.set_node(self.selected_wire, self.selected_column, circuit_grid_node)
        elif selected_node_gate_part == node_types.H:
            self.handle_input_delete()
        self.update()

    def handle_input_delete(self):
        selected_node_gate_part = self.get_selected_node_gate_part()
        if selected_node_gate_part == node_types.X or \
                selected_node_gate_part == node_types.Y or \
                selected_node_gate_part == node_types.Z or \
                selected_node_gate_part == node_types.H:
            self.delete_controls_for_gate(self.selected_wire, self.selected_column)

        if selected_node_gate_part == node_types.CTRL:
            gate_wire_num = \
                self.circuit_grid_model.get_gate_wire_for_control_node(self.selected_wire,
                                                                       self.selected_column)
            if gate_wire_num >= 0:
                self.delete_controls_for_gate(gate_wire_num,
                                              self.selected_column)
        elif selected_node_gate_part != node_types.SWAP and \
                selected_node_gate_part != node_types.CTRL and \
                selected_node_gate_part != node_types.TRACE:
            circuit_grid_node = CircuitGridNode(node_types.EMPTY)
            self.circuit_grid_model.set_node(self.selected_wire, self.selected_column, circuit_grid_node)

        self.update()

    def handle_input_ctrl(self):
        # TODO: Handle Toffoli gates. For now, control qubit is assumed to be in ctrl_a variable
        #       with ctrl_b variable reserved for Toffoli gates
        selected_node_gate_part = self.get_selected_node_gate_part()
        if selected_node_gate_part == node_types.X or \
                selected_node_gate_part == node_types.Y or \
                selected_node_gate_part == node_types.Z or \
                selected_node_gate_part == node_types.H:
            circuit_grid_node = self.circuit_grid_model.get_node(self.selected_wire, self.selected_column)
            if circuit_grid_node.ctrl_a >= 0:
                # Gate already has a control qubit so remove it
                orig_ctrl_a = circuit_grid_node.ctrl_a
                circuit_grid_node.ctrl_a = -1
                self.circuit_grid_model.set_node(self.selected_wire, self.selected_column, circuit_grid_node)

                # Remove TRACE nodes
                for wire_num in range(min(self.selected_wire, orig_ctrl_a) + 1,
                                      max(self.selected_wire, orig_ctrl_a)):
                    if self.circuit_grid_model.get_node_gate_part(wire_num,
                                                                  self.selected_column) == node_types.TRACE:
                        self.circuit_grid_model.set_node(wire_num, self.selected_column,
                                                         CircuitGridNode(node_types.EMPTY))
                self.update()
            else:
                # Attempt to place a control qubit beginning with the wire above
                if self.selected_wire >= 0:
                    if self.place_ctrl_qubit(self.selected_wire, self.selected_wire - 1) == -1:
                        if self.selected_wire < self.circuit_grid_model.max_wires:
                            if self.place_ctrl_qubit(self.selected_wire, self.selected_wire + 1) == -1:
                                print("Can't place control qubit")
                                self.display_exceptional_condition()

    def handle_input_move_ctrl(self, direction):
        # TODO: Handle Toffoli gates. For now, control qubit is assumed to be in ctrl_a variable
        #       with ctrl_b variable reserved for Toffoli gates
        # TODO: Simplify the logic in this method, including considering not actually ever
        #       placing a TRACE, but rather always dynamically calculating if a TRACE s/b displayed
        selected_node_gate_part = self.get_selected_node_gate_part()
        if selected_node_gate_part == node_types.X or \
                selected_node_gate_part == node_types.Y or \
                selected_node_gate_part == node_types.Z or \
                selected_node_gate_part == node_types.H:
            circuit_grid_node = self.circuit_grid_model.get_node(self.selected_wire, self.selected_column)
            if 0 <= circuit_grid_node.ctrl_a < self.circuit_grid_model.max_wires:
                # Gate already has a control qubit so try to move it
                if direction == MOVE_UP:
                    candidate_wire_num = circuit_grid_node.ctrl_a - 1
                    if candidate_wire_num == self.selected_wire:
                        candidate_wire_num -= 1
                else:
                    candidate_wire_num = circuit_grid_node.ctrl_a + 1
                    if candidate_wire_num == self.selected_wire:
                        candidate_wire_num += 1
                if 0 <= candidate_wire_num < self.circuit_grid_model.max_wires:
                    if self.place_ctrl_qubit(self.selected_wire, candidate_wire_num) == candidate_wire_num:
                        print("control qubit successfully placed on wire ", candidate_wire_num)
                        if direction == MOVE_UP and candidate_wire_num < self.selected_wire:
                            if self.circuit_grid_model.get_node_gate_part(candidate_wire_num + 1,
                                                                          self.selected_column) == node_types.EMPTY:
                                self.circuit_grid_model.set_node(candidate_wire_num + 1, self.selected_column,
                                                                 CircuitGridNode(node_types.TRACE))
                        elif direction == MOVE_DOWN and candidate_wire_num > self.selected_wire:
                            if self.circuit_grid_model.get_node_gate_part(candidate_wire_num - 1,
                                                                          self.selected_column) == node_types.EMPTY:
                                self.circuit_grid_model.set_node(candidate_wire_num - 1, self.selected_column,
                                                                 CircuitGridNode(node_types.TRACE))
                        self.update()
                    else:
                        print("control qubit could not be placed on wire ", candidate_wire_num)

    def handle_input_rotate(self, radians):
        selected_node_gate_part = self.get_selected_node_gate_part()
        if selected_node_gate_part == node_types.X or \
                selected_node_gate_part == node_types.Y or \
                selected_node_gate_part == node_types.Z:
            circuit_grid_node = self.circuit_grid_model.get_node(self.selected_wire, self.selected_column)
            circuit_grid_node.radians = (circuit_grid_node.radians + radians) % (2 * np.pi)
            self.circuit_grid_model.set_node(self.selected_wire, self.selected_column, circuit_grid_node)

        self.update()

    def place_ctrl_qubit(self, gate_wire_num, candidate_ctrl_wire_num):
        """Attempt to place a control qubit on a wire.
        If successful, return the wire number. If not, return -1
        """
        if candidate_ctrl_wire_num < 0 or candidate_ctrl_wire_num >= self.circuit_grid_model.max_wires:
            return -1
        candidate_wire_gate_part = \
            self.circuit_grid_model.get_node_gate_part(candidate_ctrl_wire_num,
                                                       self.selected_column)
        if candidate_wire_gate_part == node_types.EMPTY or \
                candidate_wire_gate_part == node_types.TRACE:
            circuit_grid_node = self.circuit_grid_model.get_node(gate_wire_num, self.selected_column)
            circuit_grid_node.ctrl_a = candidate_ctrl_wire_num
            self.circuit_grid_model.set_node(gate_wire_num, self.selected_column, circuit_grid_node)
            self.circuit_grid_model.set_node(candidate_ctrl_wire_num, self.selected_column,
                                             CircuitGridNode(node_types.EMPTY))
            self.update()
            return candidate_ctrl_wire_num
        else:
            print("Can't place control qubit on wire: ", candidate_ctrl_wire_num)
            return -1

    def delete_controls_for_gate(self, gate_wire_num, column_num):
        control_a_wire_num = self.circuit_grid_model.get_node(gate_wire_num, column_num).ctrl_a
        control_b_wire_num = self.circuit_grid_model.get_node(gate_wire_num, column_num).ctrl_b

        # Choose the control wire (if any exist) furthest away from the gate wire
        control_a_wire_distance = 0
        control_b_wire_distance = 0
        if control_a_wire_num >= 0:
            control_a_wire_distance = abs(control_a_wire_num - gate_wire_num)
        if control_b_wire_num >= 0:
            control_b_wire_distance = abs(control_b_wire_num - gate_wire_num)

        control_wire_num = -1
        if control_a_wire_distance > control_b_wire_distance:
            control_wire_num = control_a_wire_num
        elif control_a_wire_distance < control_b_wire_distance:
            control_wire_num = control_b_wire_num

        if control_wire_num >= 0:
            # TODO: If this is a controlled gate, remove the connecting TRACE parts between the gate and the control
            # ALSO: Refactor with similar code in this method
            for wire_idx in range(min(gate_wire_num, control_wire_num),
                                  max(gate_wire_num, control_wire_num) + 1):
                print("Replacing wire ", wire_idx, " in column ", column_num)
                circuit_grid_node = CircuitGridNode(node_types.EMPTY)
                self.circuit_grid_model.set_node(wire_idx, column_num, circuit_grid_node)


class CircuitGridBackground(pygame.sprite.Sprite):
    """Background for circuit grid"""

    def __init__(self, circuit_grid_model):
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.Surface([GRID_WIDTH * (18 + 2),
                                     GRID_HEIGHT * (3 + 1)])
        self.image.convert()
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        pygame.draw.rect(self.image, BLACK, self.rect, LINE_WIDTH)

        for wire_num in range(circuit_grid_model.max_wires):
            pygame.draw.line(self.image, BLACK,
                             (GRID_WIDTH * 0.5, (wire_num + 1) * GRID_HEIGHT),
                             (self.rect.width - (GRID_WIDTH * 0.5), (wire_num + 1) * GRID_HEIGHT),
                             LINE_WIDTH)


class CircuitGridGate(pygame.sprite.Sprite):
    """Images for nodes"""

    def __init__(self, circuit_grid_model, wire_num, column_num):
        pygame.sprite.Sprite.__init__(self)
        self.circuit_grid_model = circuit_grid_model
        self.wire_num = wire_num
        self.column_num = column_num

        self.update()

    def update(self):
        node_type = self.circuit_grid_model.get_node_gate_part(self.wire_num, self.column_num)

        if node_type == node_types.H:
            self.image, self.rect = load_image('gate_images/h_gate.png', -1)
        elif node_type == node_types.X:
            node = self.circuit_grid_model.get_node(self.wire_num, self.column_num)
            if node.ctrl_a >= 0 or node.ctrl_b >= 0:
                # This is a control-X gate or Toffoli gate
                # TODO: Handle Toffoli gates more completely
                if self.wire_num > max(node.ctrl_a, node.ctrl_b):
                    self.image, self.rect = load_image('gate_images/not_gate_below_ctrl.png', -1)
                else:
                    self.image, self.rect = load_image('gate_images/not_gate_above_ctrl.png', -1)
            elif node.radians != 0:
                self.image, self.rect = load_image('gate_images/rx_gate.png', -1)
                self.rect = self.image.get_rect()
                pygame.draw.arc(self.image, MAGENTA, self.rect, 0, node.radians % (2 * np.pi), 6)
                pygame.draw.arc(self.image, MAGENTA, self.rect, node.radians % (2 * np.pi), 2 * np.pi, 1)
            else:
                self.image, self.rect = load_image('gate_images/x_gate.png', -1)
        elif node_type == node_types.Y:
            node = self.circuit_grid_model.get_node(self.wire_num, self.column_num)
            if node.radians != 0:
                self.image, self.rect = load_image('gate_images/ry_gate.png', -1)
                self.rect = self.image.get_rect()
                pygame.draw.arc(self.image, MAGENTA, self.rect, 0, node.radians % (2 * np.pi), 6)
                pygame.draw.arc(self.image, MAGENTA, self.rect, node.radians % (2 * np.pi), 2 * np.pi, 1)
            else:
                self.image, self.rect = load_image('gate_images/y_gate.png', -1)
        elif node_type == node_types.Z:
            node = self.circuit_grid_model.get_node(self.wire_num, self.column_num)
            if node.radians != 0:
                self.image, self.rect = load_image('gate_images/rz_gate.png', -1)
                self.rect = self.image.get_rect()
                pygame.draw.arc(self.image, MAGENTA, self.rect, 0, node.radians % (2 * np.pi), 6)
                pygame.draw.arc(self.image, MAGENTA, self.rect, node.radians % (2 * np.pi), 2 * np.pi, 1)
            else:
                self.image, self.rect = load_image('gate_images/z_gate.png', -1)
        elif node_type == node_types.S:
            self.image, self.rect = load_image('gate_images/s_gate.png', -1)
        elif node_type == node_types.SDG:
            self.image, self.rect = load_image('gate_images/sdg_gate.png', -1)
        elif node_type == node_types.T:
            self.image, self.rect = load_image('gate_images/t_gate.png', -1)
        elif node_type == node_types.TDG:
            self.image, self.rect = load_image('gate_images/tdg_gate.png', -1)
        elif node_type == node_types.IDEN:
            # a completely transparent PNG is used to place at the end of the circuit to prevent crash
            # the game crashes if the circuit is empty
            self.image, self.rect = load_image('gate_images/transparent.png', -1)
        elif node_type == node_types.CTRL:
            # TODO: Handle Toffoli gates correctly
            if self.wire_num > \
                    self.circuit_grid_model.get_gate_wire_for_control_node(self.wire_num, self.column_num):
                self.image, self.rect = load_image('gate_images/ctrl_gate_bottom_wire.png', -1)
            else:
                self.image, self.rect = load_image('gate_images/ctrl_gate_top_wire.png', -1)
        elif node_type == node_types.TRACE:
            self.image, self.rect = load_image('gate_images/trace_gate.png', -1)
        elif node_type == node_types.SWAP:
            self.image, self.rect = load_image('gate_images/swap_gate.png', -1)
        else:
            self.image = pygame.Surface([GATE_TILE_WIDTH, GATE_TILE_HEIGHT])
            self.image.set_alpha(0)
            self.rect = self.image.get_rect()

        self.image.convert()


class CircuitGridCursor(pygame.sprite.Sprite):
    """Cursor to highlight current grid node"""

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('cursor_images/circuit-grid-cursor-medium.png', -1)
        self.image.convert_alpha()
