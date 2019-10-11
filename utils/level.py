import pygame

from model.circuit_grid_model import CircuitGridModel
from model import circuit_node_types as node_types
from containers.vbox import VBox
from viz.statevector_grid import StatevectorGrid
from controls.circuit_grid import CircuitGrid, CircuitGridNode
from utils.parameters import WIDTH_UNIT, CIRCUIT_DEPTH


class Level:
    """Start up a level"""
    def __init__(self):
        self.level = 3  # game level
        self.win = False  # flag for winning the game
        self.left_paddle = pygame.sprite.Sprite()
        self.right_paddle = pygame.sprite.Sprite()

    def setup(self, scene, ball):
        """Setup a level with a certain level number"""
        scene.qubit_num = self.level
        self.circuit_grid_model = CircuitGridModel(scene.qubit_num, CIRCUIT_DEPTH)

        # the game crashes if the circuit is empty
        # initialize circuit with identity gate at the end of each line to prevent crash
        # identity gate are displayed by completely transparent PNG
        for i in range(scene.qubit_num):
            self.circuit_grid_model.set_node(i, CIRCUIT_DEPTH - 1, CircuitGridNode(node_types.IDEN))

        self.circuit = self.circuit_grid_model.compute_circuit()
        self.statevector_grid = StatevectorGrid(self.circuit, scene.qubit_num, 100)
        self.right_statevector = VBox(WIDTH_UNIT * 90, WIDTH_UNIT * 0, self.statevector_grid)
        self.circuit_grid = CircuitGrid(0, ball.screenheight, self.circuit_grid_model)

        # computer paddle

        self.left_paddle.image = pygame.Surface([WIDTH_UNIT, int(round(ball.screenheight / 2 ** scene.qubit_num))])
        self.left_paddle.image.fill((255, 255, 255))
        self.left_paddle.image.set_alpha(255)
        self.left_paddle.rect = self.left_paddle.image.get_rect()
        self.left_paddle.rect.x = 9 * WIDTH_UNIT

        # player paddle for detection of collision. It is invisible on the screen

        self.right_paddle.image = pygame.Surface([WIDTH_UNIT, int(round(ball.screenheight / 2 ** scene.qubit_num))])
        self.right_paddle.image.fill((255, 0, 255))
        self.right_paddle.image.set_alpha(0)
        self.right_paddle.rect = self.right_paddle.image.get_rect()
        self.right_paddle.rect.x = self.right_statevector.xpos

    def levelup(self):
        """Increase level by 1"""
        if self.level <= 3:
            self.level += self.level
            self.setup()
        else:
            self.win = True  # win the game if level is higher than 3
