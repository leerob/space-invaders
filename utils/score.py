import pygame


class Score(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        self.player = 0
        self.computer = 0

    # Player = 0, Computer = 1
    def update(self, score):
        if score == 0:
            self.computer += 1

        if score == 1:
            self.player += 1

    def get_score(self, player):
        if player == 0:
            return self.computer
        if player == 1:
            return self.player

    def reset_score(self):
        self.computer = 0
        self.player = 0
