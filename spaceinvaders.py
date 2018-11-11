#!/usr/bin/env python

# Space Invaders
# Created by Lee Robinson

import sys
from os.path import abspath, dirname
from random import choice

from pygame import display, event, font, image, init, key,\
    mixer, time, transform, Surface
from pygame.constants import QUIT, KEYDOWN, KEYUP, USEREVENT,\
    K_ESCAPE, K_LEFT, K_RIGHT, K_SPACE
from pygame.event import Event
from pygame.mixer import Sound
from pygame.sprite import groupcollide, Group, Sprite


BASE_PATH = abspath(dirname(__file__))
FONT_PATH = BASE_PATH + '/fonts/'
IMAGE_PATH = BASE_PATH + '/images/'
SOUND_PATH = BASE_PATH + '/sounds/'

# Colors (R, G, B)
WHITE = (255, 255, 255)
GREEN = (78, 255, 87)
YELLOW = (241, 255, 0)
BLUE = (80, 255, 239)
PURPLE = (203, 0, 255)
RED = (237, 28, 36)

SCREEN = display.set_mode((800, 600))
FONT = FONT_PATH + 'space_invaders.ttf'
IMG_NAMES = ['ship', 'mystery',
             'enemy1_1', 'enemy1_2',
             'enemy2_1', 'enemy2_2',
             'enemy3_1', 'enemy3_2',
             'explosionblue', 'explosiongreen', 'explosionpurple',
             'laser', 'enemylaser']
IMAGES = {name: image.load(IMAGE_PATH + '{}.png'.format(name)).convert_alpha()
          for name in IMG_NAMES}

BLOCKERS_POSITION = 450
ENEMY_DEFAULT_POSITION = 65  # Initial value for a new game
ENEMY_MOVE_DOWN = 35
EVENT_SHIP_CREATE = USEREVENT + 0
EVENT_ENEMY_SHOOT = USEREVENT + 1
EVENT_ENEMY_MOVE_NOTE = USEREVENT + 2
SCREEN_MAIN = 1
SCREEN_GAME = 2
SCREEN_OVER = 3


class Ship(Sprite):
    def __init__(self, *groups):
        super(Ship, self).__init__(*groups)
        self.image = IMAGES['ship']
        self.rect = self.image.get_rect(topleft=(375, 540))
        self.speed = 5

    def update(self, keys, *args):
        if keys[K_LEFT] and self.rect.x > 10:
            self.rect.x -= self.speed
        if keys[K_RIGHT] and self.rect.x < 740:
            self.rect.x += self.speed
        game.screen.blit(self.image, self.rect)


class Bullet(Sprite):
    def __init__(self, x, y, velocity, filename, *groups):
        super(Bullet, self).__init__(*groups)
        self.image = IMAGES[filename]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.velocity = velocity

    def update(self, *args):
        game.screen.blit(self.image, self.rect)
        self.rect.y += self.velocity
        if self.rect.y < 15 or self.rect.y > 600:
            self.kill()


class Enemy(Sprite):
    row_scores = {0: 30, 1: 20, 2: 20, 3: 10, 4: 10}
    row_images = {0: [transform.scale(IMAGES['enemy1_2'], (40, 35)),
                      transform.scale(IMAGES['enemy1_1'], (40, 35))],
                  1: [transform.scale(IMAGES['enemy2_2'], (40, 35)),
                      transform.scale(IMAGES['enemy2_1'], (40, 35))],
                  2: [transform.scale(IMAGES['enemy2_2'], (40, 35)),
                      transform.scale(IMAGES['enemy2_1'], (40, 35))],
                  3: [transform.scale(IMAGES['enemy3_1'], (40, 35)),
                      transform.scale(IMAGES['enemy3_2'], (40, 35))],
                  4: [transform.scale(IMAGES['enemy3_1'], (40, 35)),
                      transform.scale(IMAGES['enemy3_2'], (40, 35))]}

    def __init__(self, x, y, row, column, *groups):
        self.row = row
        self.column = column
        super(Enemy, self).__init__(*groups)
        self.images = Enemy.row_images[self.row]
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.score = self.row_scores[self.row]

    def toggle_image(self):
        self.index += 1
        if self.index >= len(self.images):
            self.index = 0
        self.image = self.images[self.index]

    def update(self, *args):
        game.screen.blit(self.image, self.rect)


class EnemiesGroup(Group):
    def __init__(self, columns, rows):
        super(EnemiesGroup, self).__init__()
        self.enemies = [[None] * columns for _ in range(rows)]
        self.columns = columns
        self.rows = rows
        self.leftAddMove = 0
        self.rightAddMove = 0
        self.moveTime = 600
        self.direction = 1
        self.rightMoves = 30
        self.leftMoves = 30
        self.moveNumber = 15
        self.timer = time.get_ticks()
        self.bottom = game.enemyPosition + ((rows - 1) * 45) + 35
        self._aliveColumns = list(range(columns))
        self._leftAliveColumn = 0
        self._rightAliveColumn = columns - 1
        self._leftDeadColumns = 0
        self._rightDeadColumns = 0

    def update(self, current_time):
        if current_time - self.timer > self.moveTime:
            if self.direction == 1:
                max_move = self.rightMoves + self.rightAddMove
            else:
                max_move = self.leftMoves + self.leftAddMove

            if self.moveNumber >= max_move:
                if self.direction == 1:
                    self.leftMoves = 30 + self.rightAddMove
                elif self.direction == -1:
                    self.rightMoves = 30 + self.leftAddMove
                self.direction *= -1
                self.moveNumber = 0
                self.bottom += ENEMY_MOVE_DOWN
                for enemy in self:
                    enemy.rect.y += ENEMY_MOVE_DOWN
                    enemy.toggle_image()
            else:
                velocity = 10 if self.direction == 1 else -10
                for enemy in self:
                    enemy.rect.x += velocity
                    enemy.toggle_image()
                self.moveNumber += 1

            self.timer += self.moveTime
            event.post(Event(EVENT_ENEMY_MOVE_NOTE, {}))

    def add_internal(self, *sprites):
        super(EnemiesGroup, self).add_internal(*sprites)
        for s in sprites:
            self.enemies[s.row][s.column] = s

    def remove_internal(self, *sprites):
        super(EnemiesGroup, self).remove_internal(*sprites)
        for s in sprites:
            self._kill(s)
        self._update_speed()

    def is_column_dead(self, column):
        return not any(self.enemies[row][column]
                       for row in range(self.rows))

    def random_bottom(self):
        # type: () -> Optional[Enemy]
        col = choice(self._aliveColumns)
        col_enemies = (self.enemies[row - 1][col]
                       for row in range(self.rows, 0, -1))
        return next((en for en in col_enemies if en is not None), None)

    def _update_speed(self):
        if len(self) == 1:
            self.moveTime = 200
        elif len(self) <= 10:
            self.moveTime = 400

    def _kill(self, enemy):
        self.enemies[enemy.row][enemy.column] = None
        is_column_dead = self.is_column_dead(enemy.column)
        if is_column_dead:
            self._aliveColumns.remove(enemy.column)

        if enemy.column == self._rightAliveColumn:
            while self._rightAliveColumn > 0 and is_column_dead:
                self._rightAliveColumn -= 1
                self._rightDeadColumns += 1
                self.rightAddMove += 5
                is_column_dead = self.is_column_dead(self._rightAliveColumn)

        elif enemy.column == self._leftAliveColumn:
            while self._leftAliveColumn < self.columns and is_column_dead:
                self._leftAliveColumn += 1
                self._leftDeadColumns += 1
                self.leftAddMove += 5
                is_column_dead = self.is_column_dead(self._leftAliveColumn)


class Blocker(Sprite):
    def __init__(self, x, y, size, color_, *groups):
        super(Blocker, self).__init__(*groups)
        self.image = Surface((size, size))
        self.image.fill(color_)
        self.rect = self.image.get_rect(topleft=(x, y))

    def update(self, *args):
        game.screen.blit(self.image, self.rect)


class Mystery(Sprite):
    def __init__(self, *groups):
        super(Mystery, self).__init__(*groups)
        self.image = transform.scale(IMAGES['mystery'], (75, 35))
        self.rect = self.image.get_rect(topleft=(-80, 45))
        self.moveTime = 25000
        self.velocity = 2
        self.timer = time.get_ticks()
        self.mysteryEntered = Sound(SOUND_PATH + 'mysteryentered.wav')
        self.mysteryEntered.set_volume(0.3)
        self.playSound = True
        self.score = choice([50, 100, 150, 300])

    # noinspection PyUnusedLocal
    def update(self, keys, current_time, *args):
        passed = current_time - self.timer
        if passed > self.moveTime:
            if (self.rect.x < 0 or self.rect.x > 800) and self.playSound:
                self.mysteryEntered.play()
                self.playSound = False
            if -100 < self.rect.x < 840:
                self.mysteryEntered.fadeout(4000)
                self.rect.x += self.velocity
                game.screen.blit(self.image, self.rect)
            if self.rect.x < -90 or self.rect.x > 830:
                self.playSound = True
                self.velocity *= -1
                self.timer = current_time


class EnemyExplosion(Sprite):
    def __init__(self, enemy, *groups):
        super(EnemyExplosion, self).__init__(*groups)
        self.image = transform.scale(self.get_image(enemy.row), (40, 35))
        self.image2 = transform.scale(self.image, (50, 45))
        self.rect = self.image.get_rect(topleft=(enemy.rect.x, enemy.rect.y))
        self.timer = time.get_ticks()

    @staticmethod
    def get_image(row):
        img_colors = ['purple', 'blue', 'blue', 'green', 'green']
        return IMAGES['explosion{}'.format(img_colors[row])]

    def update(self, current_time):
        passed = current_time - self.timer
        if passed <= 100:
            game.screen.blit(self.image, self.rect)
        elif passed <= 200:
            game.screen.blit(self.image2, (self.rect.x - 6, self.rect.y - 6))
        elif 400 < passed:
            self.kill()


class MysteryExplosion(Sprite):
    def __init__(self, mystery, *groups):
        super(MysteryExplosion, self).__init__(*groups)
        self.text = Txt(FONT, 20, str(mystery.score), WHITE,
                        mystery.rect.x + 20, mystery.rect.y + 6)
        self.timer = time.get_ticks()

    def update(self, current_time):
        passed = current_time - self.timer
        if passed <= 200 or 400 < passed <= 600:
            self.text.update()
        elif 600 < passed:
            self.kill()


class ShipExplosion(Sprite):
    def __init__(self, ship, *groups):
        super(ShipExplosion, self).__init__(*groups)
        self.image = IMAGES['ship']
        self.rect = self.image.get_rect(topleft=(ship.rect.x, ship.rect.y))
        self.timer = time.get_ticks()

    def update(self, current_time):
        passed = current_time - self.timer
        if 300 < passed <= 600:
            game.screen.blit(self.image, self.rect)
        elif 900 < passed:
            self.kill()
            event.post(Event(EVENT_SHIP_CREATE, {}))


class Img(Sprite):
    def __init__(self, x, y, filename, w, h, *groups):
        super(Img, self).__init__(*groups)
        self.image = transform.scale(IMAGES[filename], (w, h))
        self.rect = self.image.get_rect(topleft=(x, y))

    def update(self, *args):
        game.screen.blit(self.image, self.rect)


class Txt(Sprite):
    def __init__(self, font_, size, message, color_, x, y, *groups):
        super(Txt, self).__init__(*groups)
        self.font = font.Font(font_, size)
        self.image = self.font.render(str(message), True, color_)
        self.rect = self.image.get_rect(topleft=(x, y))

    def update(self, *args):
        game.screen.blit(self.image, self.rect)


class SpaceInvaders(object):
    def __init__(self):
        # It seems, in Linux buffersize=512 is not enough, use 4096 to prevent:
        #   ALSA lib pcm.c:7963:(snd_pcm_recover) underrun occurred
        mixer.pre_init(44100, -16, 1, 4096)
        init()
        # Init sounds
        self.sounds = {}
        for name in ['shoot', 'shoot2', 'invaderkilled', 'mysterykilled',
                     'shipexplosion']:
            self.sounds[name] = Sound(SOUND_PATH + '{}.wav'.format(name))
            self.sounds[name].set_volume(0.2)
        # Init notes
        self.musicNotes = [Sound(SOUND_PATH + '{}.wav'.format(i))
                           for i in range(4)]
        for note in self.musicNotes:
            note.set_volume(0.5)
        self.noteIndex = 0

        self.caption = display.set_caption('Space Invaders')
        self.screen = SCREEN
        self.background = image.load(IMAGE_PATH + 'background.jpg').convert()
        self.screenType = SCREEN_MAIN
        # Counter for enemy starting position (increased each new round)
        self.enemyPosition = ENEMY_DEFAULT_POSITION

        self.mainScreenGroup = Group(
            Txt(FONT, 50, 'Space Invaders', WHITE, 164, 155),
            Txt(FONT, 25, 'Press any key to continue', WHITE, 201, 225),
            Img(318, 270, 'enemy3_1', 40, 40),
            Txt(FONT, 25, '   =   10 pts', GREEN, 368, 270),
            Img(318, 320, 'enemy2_2', 40, 40),
            Txt(FONT, 25, '   =  20 pts', BLUE, 368, 320),
            Img(318, 370, 'enemy1_2', 40, 40),
            Txt(FONT, 25, '   =  30 pts', PURPLE, 368, 370),
            Img(299, 420, 'mystery', 80, 40),
            Txt(FONT, 25, '   =  ?????', RED, 368, 420),
        )
        self.gameOverTxt = Txt(FONT, 50, 'Game Over', WHITE, 250, 270)
        self.nextRoundTxt = Txt(FONT, 50, 'Next Round', WHITE, 240, 270)

        self.allSprites = Group()
        self.bullets = Group()
        self.enemyBullets = Group()
        self.explosionsGroup = Group()
        self.playerGroup = Group()
        self.mysteryGroup = Group()
        self.allBlockers = Group()
        self.score = 0
        self.dashGroup = Group(Txt(FONT, 20, 'Score', WHITE, 5, 5),
                               Txt(FONT, 20, 'Lives ', WHITE, 640, 5))
        self.scoreTxt = Txt(FONT, 20, self.score, GREEN, 85, 5, self.dashGroup)
        self.life1 = Img(715, 3, 'ship', 23, 23, self.dashGroup)
        self.life2 = Img(742, 3, 'ship', 23, 23, self.dashGroup)
        self.life3 = Img(769, 3, 'ship', 23, 23, self.dashGroup)

        self.clock = time.Clock()

    def reset(self):
        for gr in (self.allSprites, self.playerGroup, self.explosionsGroup,
                   self.bullets, self.mysteryGroup, self.enemyBullets):
            gr.empty()
        self.player = Ship(self.allSprites, self.playerGroup)
        Mystery(self.allSprites, self.mysteryGroup)
        self.make_enemies()
        self.noteIndex = 0
        event.clear()
        time.set_timer(EVENT_ENEMY_SHOOT, 700)

    @staticmethod
    def make_blockers(offset):
        blocker_group = Group()
        for row in range(4):
            for column in range(9):
                x = 50 + offset + (column * 10)
                y = BLOCKERS_POSITION + (row * 10)
                Blocker(x, y, 10, GREEN, blocker_group)
        return blocker_group

    @staticmethod
    def should_exit(evt):
        # type: (event.EventType) -> bool
        return evt.type == QUIT or (evt.type == KEYUP and evt.key == K_ESCAPE)

    def check_input(self):
        for e in event.get():
            if self.should_exit(e):
                sys.exit()
            elif e.type == KEYDOWN:
                if e.key == K_SPACE:
                    if not self.bullets and self.player.alive():
                        y = self.player.rect.y + 5
                        if self.score < 1000:
                            Bullet(self.player.rect.x + 23, y, -15, 'laser',
                                   self.bullets, self.allSprites)
                            self.sounds['shoot'].play()
                        else:
                            Bullet(self.player.rect.x + 8, y, -15, 'laser',
                                   self.bullets, self.allSprites)
                            Bullet(self.player.rect.x + 38, y, -15, 'laser',
                                   self.bullets, self.allSprites)
                            self.sounds['shoot2'].play()
            elif e.type == EVENT_SHIP_CREATE:
                self.player = Ship(self.allSprites, self.playerGroup)
            elif e.type == EVENT_ENEMY_SHOOT and self.enemies:
                enemy = self.enemies.random_bottom()
                Bullet(enemy.rect.x + 14, enemy.rect.y + 20, 5, 'enemylaser',
                       self.enemyBullets, self.allSprites)
            elif e.type == EVENT_ENEMY_MOVE_NOTE:
                self.musicNotes[self.noteIndex].play()
                self.noteIndex += 1
                if self.noteIndex >= len(self.musicNotes):
                    self.noteIndex = 0

    def make_enemies(self):
        enemies = EnemiesGroup(10, 5)
        for row in range(5):
            for column in range(10):
                x = 157 + (column * 50)
                y = self.enemyPosition + (row * 45)
                Enemy(x, y, row, column, enemies, self.allSprites)
        enemies.bottom = self.enemyPosition + (4 * 45) + 35
        self.enemies = enemies

    def inc_score(self, score):
        self.score += score
        self.scoreTxt.kill()
        self.scoreTxt = Txt(FONT, 20, self.score, GREEN, 85, 5, self.dashGroup)

    def check_collisions(self):
        groupcollide(self.bullets, self.enemyBullets, True, True)

        for enemy in groupcollide(self.enemies, self.bullets,
                                  True, True).keys():
            self.sounds['invaderkilled'].play()
            self.inc_score(enemy.score)
            EnemyExplosion(enemy, self.explosionsGroup)
            self.gameTimer = time.get_ticks()

        for mystery in groupcollide(self.mysteryGroup, self.bullets,
                                    True, True).keys():
            mystery.mysteryEntered.stop()
            self.sounds['mysterykilled'].play()
            self.inc_score(mystery.score)
            MysteryExplosion(mystery, self.explosionsGroup)
            Mystery(self.allSprites, self.mysteryGroup)

        for playerShip in groupcollide(self.playerGroup, self.enemyBullets,
                                       True, True).keys():
            if self.life3.alive():
                self.life3.kill()
            elif self.life2.alive():
                self.life2.kill()
            elif self.life1.alive():
                self.life1.kill()
            else:
                self.screenType = SCREEN_OVER
                self.gameTimer = time.get_ticks()
            self.sounds['shipexplosion'].play()
            ShipExplosion(playerShip, self.explosionsGroup)

        if self.enemies.bottom >= 540:
            groupcollide(self.enemies, self.playerGroup, True, True)
            if not self.player.alive() or self.enemies.bottom >= 600:
                self.screenType = SCREEN_OVER
                self.gameTimer = time.get_ticks()

        groupcollide(self.bullets, self.allBlockers, True, True)
        groupcollide(self.enemyBullets, self.allBlockers, True, True)
        # It's too hard to calc 50 en * 144 bl = 7200 collisions with 60 FPS.
        # Calc if really needed.
        if self.enemies.bottom >= BLOCKERS_POSITION:
            groupcollide(self.enemies, self.allBlockers, False, True)

    def main(self):
        while True:
            self.screen.blit(self.background, (0, 0))
            current_time = time.get_ticks()
            if self.screenType == SCREEN_MAIN:
                self.mainScreenGroup.update()

                for e in event.get():
                    if self.should_exit(e):
                        sys.exit()
                    elif e.type == KEYUP:
                        self.reset()
                        # Only create blockers on a new game, not a new round
                        self.allBlockers.empty()
                        self.allBlockers.add(self.make_blockers(0),
                                             self.make_blockers(200),
                                             self.make_blockers(400),
                                             self.make_blockers(600))
                        self.inc_score(-self.score)  # Set zero score
                        self.dashGroup.add(self.life1, self.life2, self.life3)
                        self.screenType = SCREEN_GAME

            elif self.screenType == SCREEN_GAME:
                self.dashGroup.update()

                if not self.enemies and not self.explosionsGroup:
                    passed = current_time - self.gameTimer
                    if passed <= 3000:
                        self.nextRoundTxt.update()
                    elif 3000 < passed:
                        # Move enemies closer to bottom
                        self.enemyPosition += ENEMY_MOVE_DOWN
                        self.reset()
                else:
                    self.allBlockers.update()
                    self.check_input()
                    keys = key.get_pressed()
                    self.enemies.update(current_time)
                    self.allSprites.update(keys, current_time)
                    self.explosionsGroup.update(current_time)
                    self.check_collisions()

            elif self.screenType == SCREEN_OVER:
                # Reset enemy start position
                self.enemyPosition = ENEMY_DEFAULT_POSITION
                passed = current_time - self.gameTimer
                if passed < 750 or 1500 < passed < 2250:
                    self.gameOverTxt.update()
                elif 3000 < passed:
                    self.screenType = SCREEN_MAIN

                for e in event.get():
                    if self.should_exit(e):
                        sys.exit()

            display.update()
            self.clock.tick(60)


if __name__ == '__main__':
    game = SpaceInvaders()
    game.main()
