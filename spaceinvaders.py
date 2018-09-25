#!/usr/bin/env python

# Space Invaders
# Created by Lee Robinson

import sys
from os.path import abspath, dirname
from random import randint, choice

from pygame import display, event, font, image, init, key,\
    mixer, time, transform, Surface
from pygame.constants import QUIT, KEYDOWN, KEYUP,\
    K_ESCAPE, K_LEFT, K_RIGHT, K_SPACE
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


class Ship(Sprite):
    def __init__(self, *groups):
        Sprite.__init__(self, *groups)
        self.image = IMAGES['ship']
        self.rect = self.image.get_rect(topleft=(375, 540))
        self.speed = 5

    # noinspection PyUnusedLocal
    def update(self, keys, *args):
        if keys[K_LEFT] and self.rect.x > 10:
            self.rect.x -= self.speed
        if keys[K_RIGHT] and self.rect.x < 740:
            self.rect.x += self.speed
        game.screen.blit(self.image, self.rect)


class Bullet(Sprite):
    def __init__(self, x, y, velocity, filename, *groups):
        Sprite.__init__(self, *groups)
        self.image = IMAGES[filename]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.velocity = velocity

    def update(self, *args):
        game.screen.blit(self.image, self.rect)
        self.rect.y += self.velocity
        if self.rect.y < 15 or self.rect.y > 600:
            self.kill()


class Enemy(Sprite):
    def __init__(self, row, column):
        Sprite.__init__(self)
        self.row = row
        self.column = column
        self.images = []
        self.load_images()
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.direction = 1
        self.rightMoves = 30
        self.leftMoves = 30
        self.moveNumber = 15
        self.moveTime = 600
        self.timer = time.get_ticks()

    # noinspection PyUnusedLocal
    def update(self, keys, current_time, enemies):
        if current_time - self.timer > self.moveTime:
            if self.direction == 1:
                max_move = self.rightMoves + enemies.rightAddMove
            else:
                max_move = self.leftMoves + enemies.leftAddMove

            if self.moveNumber >= max_move:
                if self.direction == 1:
                    self.leftMoves = 30 + enemies.rightAddMove
                elif self.direction == -1:
                    self.rightMoves = 30 + enemies.leftAddMove
                self.direction *= -1
                self.moveNumber = 0
                self.rect.y += 35
            elif self.direction == 1:
                self.rect.x += 10
                self.moveNumber += 1
            elif self.direction == -1:
                self.rect.x -= 10
                self.moveNumber += 1

            self.index += 1
            if self.index >= len(self.images):
                self.index = 0
            self.image = self.images[self.index]

            self.timer += self.moveTime

        game.screen.blit(self.image, self.rect)

    def load_images(self):
        images = {0: ['1_2', '1_1'],
                  1: ['2_2', '2_1'],
                  2: ['2_2', '2_1'],
                  3: ['3_1', '3_2'],
                  4: ['3_1', '3_2'],
                  }
        img1, img2 = (IMAGES['enemy{}'.format(img_num)] for img_num in
                      images[self.row])
        self.images.append(transform.scale(img1, (40, 35)))
        self.images.append(transform.scale(img2, (40, 35)))


class EnemiesGroup(Group):
    def __init__(self, columns, rows):
        Group.__init__(self)
        self.enemies = [[None] * columns for _ in range(rows)]
        self.columns = columns
        self.rows = rows
        self.leftAddMove = 0
        self.rightAddMove = 0
        self._aliveColumns = list(range(columns))
        self._leftAliveColumn = 0
        self._rightAliveColumn = columns - 1
        self._leftDeadColumns = 0
        self._rightDeadColumns = 0

    def add(self, *sprites):
        super(Group, self).add(*sprites)

        for s in sprites:
            self.enemies[s.row][s.column] = s

    def is_column_dead(self, column):
        for row in range(self.rows):
            if self.enemies[row][column]:
                return False
        return True

    def random_bottom(self):
        # type: () -> Optional[Enemy]
        random_index = randint(0, len(self._aliveColumns) - 1)
        col = self._aliveColumns[random_index]
        for row in range(self.rows, 0, -1):
            enemy = self.enemies[row - 1][col]
            if enemy:
                return enemy
        return None

    def kill(self, enemy):
        # On double hit calls twice for same enemy, so check before
        if not self.enemies[enemy.row][enemy.column]:
            return  # Already dead

        self.enemies[enemy.row][enemy.column] = None
        is_column_dead = self.is_column_dead(enemy.column)
        if is_column_dead:
            self._aliveColumns.remove(enemy.column)

        if enemy.column == self._rightAliveColumn:
            while self._rightAliveColumn > 0 and is_column_dead:
                self._rightAliveColumn -= 1
                self._rightDeadColumns += 1
                self.rightAddMove = self._rightDeadColumns * 5
                is_column_dead = self.is_column_dead(self._rightAliveColumn)

        elif enemy.column == self._leftAliveColumn:
            while self._leftAliveColumn < self.columns and is_column_dead:
                self._leftAliveColumn += 1
                self._leftDeadColumns += 1
                self.leftAddMove = self._leftDeadColumns * 5
                is_column_dead = self.is_column_dead(self._leftAliveColumn)


class Blocker(Sprite):
    def __init__(self, x, y, size, color_, *groups):
        Sprite.__init__(self, *groups)
        self.image = Surface((size, size))
        self.image.fill(color_)
        self.rect = self.image.get_rect(topleft=(x, y))

    def update(self, *args):
        game.screen.blit(self.image, self.rect)


class Mystery(Sprite):
    def __init__(self, *groups):
        Sprite.__init__(self, *groups)
        self.image = IMAGES['mystery']
        self.image = transform.scale(self.image, (75, 35))
        self.rect = self.image.get_rect(topleft=(-80, 45))
        self.row = 5
        self.moveTime = 25000
        self.direction = 1
        self.timer = time.get_ticks()
        self.mysteryEntered = mixer.Sound(SOUND_PATH + 'mysteryentered.wav')
        self.mysteryEntered.set_volume(0.3)
        self.playSound = True

    # noinspection PyUnusedLocal
    def update(self, keys, current_time, *args):
        reset_timer = False
        passed = current_time - self.timer
        if passed > self.moveTime:
            if (self.rect.x < 0 or self.rect.x > 800) and self.playSound:
                self.mysteryEntered.play()
                self.playSound = False
            if self.rect.x < 840 and self.direction == 1:
                self.mysteryEntered.fadeout(4000)
                self.rect.x += 2
                game.screen.blit(self.image, self.rect)
            elif self.rect.x > -100 and self.direction == -1:
                self.mysteryEntered.fadeout(4000)
                self.rect.x -= 2
                game.screen.blit(self.image, self.rect)

        if self.rect.x > 830:
            self.playSound = True
            self.direction = -1
            reset_timer = True
        elif self.rect.x < -90:
            self.playSound = True
            self.direction = 1
            reset_timer = True
        if passed > self.moveTime and reset_timer:
            self.timer = current_time


class EnemyExplosion(Sprite):
    def __init__(self, x, y, row, *groups):
        Sprite.__init__(self, *groups)
        self.image = transform.scale(self.get_image(row), (40, 35))
        self.image2 = transform.scale(self.image, (50, 45))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.timer = time.get_ticks()

    @staticmethod
    def get_image(row):
        img_colors = ['purple', 'blue', 'blue', 'green', 'green']
        return IMAGES['explosion{}'.format(img_colors[row])]

    def update(self, current_time):
        passed = current_time - self.timer
        if passed <= 100:
            game.screen.blit(self.image, self.rect)
        elif 100 < passed <= 200:
            game.screen.blit(self.image2, (self.rect.x - 6, self.rect.y - 6))
        elif passed > 400:
            self.kill()


class MysteryExplosion(Sprite):
    def __init__(self, x, y, score, *groups):
        Sprite.__init__(self, *groups)
        self.text = Text(FONT, 20, str(score), WHITE, x + 20, y + 6)
        self.timer = time.get_ticks()

    def update(self, current_time):
        passed = current_time - self.timer
        if passed <= 200:
            self.text.draw(game.screen)
        elif 400 < passed <= 600:
            self.text.draw(game.screen)
        elif passed > 600:
            self.kill()


class ShipExplosion(Sprite):
    def __init__(self, x, y, *groups):
        Sprite.__init__(self, *groups)
        self.image = IMAGES['ship']
        self.rect = self.image.get_rect(topleft=(x, y))
        self.timer = time.get_ticks()

    def update(self, current_time):
        passed = current_time - self.timer
        if 300 < passed <= 600:
            game.screen.blit(self.image, self.rect)
        elif passed > 900:
            self.kill()


class Life(Sprite):
    def __init__(self, x, y, *groups):
        Sprite.__init__(self, *groups)
        self.image = IMAGES['ship']
        self.image = transform.scale(self.image, (23, 23))
        self.rect = self.image.get_rect(topleft=(x, y))

    def update(self, *args):
        game.screen.blit(self.image, self.rect)


class Text(object):
    def __init__(self, text_font, size, message, color_, xpos, ypos):
        self.font = font.Font(text_font, size)
        self.surface = self.font.render(message, True, color_)
        self.rect = self.surface.get_rect(topleft=(xpos, ypos))

    def draw(self, surface):
        surface.blit(self.surface, self.rect)


class SpaceInvaders(object):
    def __init__(self):
        # It seems, in Linux buffersize=512 is not enough, use 4096 to prevent:
        #   ALSA lib pcm.c:7963:(snd_pcm_recover) underrun occurred
        mixer.pre_init(44100, -16, 1, 4096)
        init()
        self.caption = display.set_caption('Space Invaders')
        self.screen = SCREEN
        self.background = image.load(IMAGE_PATH + 'background.jpg').convert()
        self.startGame = False
        self.mainScreen = True
        self.gameOver = False
        # Initial value for a new game
        self.enemyPositionDefault = 65
        # Counter for enemy starting position (increased each new round)
        self.enemyPositionStart = self.enemyPositionDefault
        # Current enemy starting position
        self.enemyPosition = self.enemyPositionStart

        self.enemy1 = transform.scale(IMAGES['enemy3_1'], (40, 40))
        self.enemy2 = transform.scale(IMAGES['enemy2_2'], (40, 40))
        self.enemy3 = transform.scale(IMAGES['enemy1_2'], (40, 40))
        self.enemy4 = transform.scale(IMAGES['mystery'], (80, 40))

        self.bullets = Group()
        self.enemyBullets = Group()
        self.explosionsGroup = Group()
        self.playerGroup = Group()
        self.mysteryGroup = Group()
        self.allBlockers = Group()
        self.livesGroup = Group()
        self.life1 = Life(715, 3, self.livesGroup)
        self.life2 = Life(742, 3, self.livesGroup)
        self.life3 = Life(769, 3, self.livesGroup)

    def reset(self, score, lives, new_game=False):
        self.playerGroup.empty()
        self.player = Ship(self.playerGroup)
        self.explosionsGroup.empty()
        self.bullets.empty()
        self.mysteryGroup.empty()
        self.mysteryShip = Mystery(self.mysteryGroup)
        self.enemyBullets.empty()
        self.reset_lives(lives)
        self.enemyPosition = self.enemyPositionStart
        self.make_enemies()
        # Only create blockers on a new game, not a new round
        if new_game:
            self.allBlockers.empty()
            self.allBlockers.add(self.make_blockers(0),
                                 self.make_blockers(200),
                                 self.make_blockers(400),
                                 self.make_blockers(600))
        self.clock = time.Clock()
        self.timer = time.get_ticks()
        self.noteTimer = time.get_ticks()
        self.shipTimer = time.get_ticks()
        self.score = score
        self.create_audio()
        self.create_text()
        self.makeNewShip = False
        self.shipAlive = True

    @staticmethod
    def make_blockers(offset):
        blocker_group = Group()
        for row in range(4):
            for column in range(9):
                x = 50 + offset + (column * 10)
                y = 450 + (row * 10)
                Blocker(x, y, 10, GREEN, blocker_group)
        return blocker_group

    def reset_lives(self, lives):
        self.livesGroup.empty()
        if lives == 3:
            self.livesGroup.add(self.life1, self.life2, self.life3)
        elif lives == 2:
            self.livesGroup.add(self.life1, self.life2)
        elif lives == 1:
            self.livesGroup.add(self.life1)

    def create_audio(self):
        self.sounds = {}
        for sound_name in ['shoot', 'shoot2', 'invaderkilled', 'mysterykilled',
                           'shipexplosion']:
            self.sounds[sound_name] = mixer.Sound(
                SOUND_PATH + '{}.wav'.format(sound_name))
            self.sounds[sound_name].set_volume(0.2)

        self.musicNotes = [mixer.Sound(SOUND_PATH + '{}.wav'.format(i)) for i
                           in range(4)]
        for sound in self.musicNotes:
            sound.set_volume(0.5)

        self.noteIndex = 0

    def play_main_music(self, current_time):
        move_time = self.enemies.sprites()[0].moveTime
        if current_time - self.noteTimer > move_time:
            self.note = self.musicNotes[self.noteIndex]
            if self.noteIndex < 3:
                self.noteIndex += 1
            else:
                self.noteIndex = 0

            self.note.play()
            self.noteTimer += move_time

    def create_text(self):
        self.titleText = Text(FONT, 50, 'Space Invaders', WHITE, 164, 155)
        self.titleText2 = Text(FONT, 25, 'Press any key to continue', WHITE,
                               201, 225)
        self.gameOverText = Text(FONT, 50, 'Game Over', WHITE, 250, 270)
        self.nextRoundText = Text(FONT, 50, 'Next Round', WHITE, 240, 270)
        self.enemy1Text = Text(FONT, 25, '   =   10 pts', GREEN, 368, 270)
        self.enemy2Text = Text(FONT, 25, '   =  20 pts', BLUE, 368, 320)
        self.enemy3Text = Text(FONT, 25, '   =  30 pts', PURPLE, 368, 370)
        self.enemy4Text = Text(FONT, 25, '   =  ?????', RED, 368, 420)
        self.scoreText = Text(FONT, 20, 'Score', WHITE, 5, 5)
        self.livesText = Text(FONT, 20, 'Lives ', WHITE, 640, 5)

    @staticmethod
    def should_exit(evt):
        # type: (event.EventType) -> bool
        return evt.type == QUIT or (evt.type == KEYUP and evt.key == K_ESCAPE)

    def check_input(self):
        for e in event.get():
            if self.should_exit(e):
                sys.exit()
            if e.type == KEYDOWN:
                if e.key == K_SPACE:
                    if len(self.bullets) == 0 and self.shipAlive:
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

    def make_enemies(self):
        enemies = EnemiesGroup(10, 5)
        for row in range(5):
            for column in range(10):
                enemy = Enemy(row, column)
                enemy.rect.x = 157 + (column * 50)
                enemy.rect.y = self.enemyPosition + (row * 45)
                enemies.add(enemy)

        self.enemies = enemies
        self.allSprites = Group(self.player, self.enemies,
                                self.livesGroup, self.mysteryShip)

    def make_enemies_shoot(self):
        if (time.get_ticks() - self.timer) > 700:
            enemy = self.enemies.random_bottom()
            if enemy:
                Bullet(enemy.rect.x + 14, enemy.rect.y + 20, 5, 'enemylaser',
                       self.enemyBullets, self.allSprites)
                self.timer = time.get_ticks()

    def calculate_score(self, row):
        scores = {0: 30,
                  1: 20,
                  2: 20,
                  3: 10,
                  4: 10,
                  5: choice([50, 100, 150, 300])
                  }

        score = scores[row]
        self.score += score
        return score

    def create_main_menu(self):
        self.screen.blit(self.enemy1, (318, 270))
        self.screen.blit(self.enemy2, (318, 320))
        self.screen.blit(self.enemy3, (318, 370))
        self.screen.blit(self.enemy4, (299, 420))

        for e in event.get():
            if self.should_exit(e):
                sys.exit()
            if e.type == KEYUP:
                self.startGame = True
                self.mainScreen = False

    def update_enemy_speed(self):
        if len(self.enemies) <= 10:
            for enemy in self.enemies:
                enemy.moveTime = 400
        if len(self.enemies) == 1:
            for enemy in self.enemies:
                enemy.moveTime = 200

    def check_collisions(self):
        groupcollide(self.bullets, self.enemyBullets, True, True)

        # Don't kill B, because of on double hit second bullet fly through an
        # explosion and kills next enemy also. And we need one dead enemy only.
        enemiesdict = groupcollide(self.bullets, self.enemies,
                                   True, False)
        if enemiesdict:
            for value in enemiesdict.values():
                for enemy in value:
                    self.enemies.kill(enemy)
                    self.sounds['invaderkilled'].play()
                    self.calculate_score(enemy.row)
                    EnemyExplosion(enemy.rect.x, enemy.rect.y, enemy.row,
                                   self.explosionsGroup)
                    self.allSprites.remove(enemy)
                    self.enemies.remove(enemy)
                    self.gameTimer = time.get_ticks()
                    break

        mysterydict = groupcollide(self.bullets, self.mysteryGroup,
                                   True, True)
        if mysterydict:
            for value in mysterydict.values():
                for mystery in value:
                    mystery.mysteryEntered.stop()
                    self.sounds['mysterykilled'].play()
                    score = self.calculate_score(mystery.row)
                    MysteryExplosion(mystery.rect.x, mystery.rect.y, score,
                                     self.explosionsGroup)
                    new_ship = Mystery()
                    self.allSprites.add(new_ship)
                    self.mysteryGroup.add(new_ship)
                    break

        bulletsdict = groupcollide(self.enemyBullets, self.playerGroup,
                                   True, True)
        if bulletsdict:
            for value in bulletsdict.values():
                for playerShip in value:
                    if self.livesGroup.has(self.life3):
                        self.life3.kill()
                    elif self.livesGroup.has(self.life2):
                        self.life2.kill()
                    elif self.livesGroup.has(self.life1):
                        self.life1.kill()
                    else:
                        self.gameOver = True
                        self.startGame = False
                    self.sounds['shipexplosion'].play()
                    ShipExplosion(playerShip.rect.x, playerShip.rect.y,
                                  self.explosionsGroup)
                    self.makeNewShip = True
                    self.shipTimer = time.get_ticks()
                    self.shipAlive = False

        if groupcollide(self.enemies, self.playerGroup, True, True):
            self.gameOver = True
            self.startGame = False

        groupcollide(self.bullets, self.allBlockers, True, True)
        groupcollide(self.enemyBullets, self.allBlockers, True, True)
        groupcollide(self.enemies, self.allBlockers, False, True)

    def create_new_ship(self, create_ship, current_time):
        if create_ship and (current_time - self.shipTimer > 900):
            self.player = Ship()
            self.allSprites.add(self.player)
            self.playerGroup.add(self.player)
            self.makeNewShip = False
            self.shipAlive = True

    def create_game_over(self, current_time):
        self.screen.blit(self.background, (0, 0))
        passed = current_time - self.timer
        if passed < 750:
            self.gameOverText.draw(self.screen)
        elif 750 < passed < 1500:
            self.screen.blit(self.background, (0, 0))
        elif 1500 < passed < 2250:
            self.gameOverText.draw(self.screen)
        elif 2250 < passed < 2750:
            self.screen.blit(self.background, (0, 0))
        elif passed > 3000:
            self.mainScreen = True

        for e in event.get():
            if self.should_exit(e):
                sys.exit()

    def main(self):
        while True:
            if self.mainScreen:
                self.reset(0, 3, True)
                self.screen.blit(self.background, (0, 0))
                self.titleText.draw(self.screen)
                self.titleText2.draw(self.screen)
                self.enemy1Text.draw(self.screen)
                self.enemy2Text.draw(self.screen)
                self.enemy3Text.draw(self.screen)
                self.enemy4Text.draw(self.screen)
                self.create_main_menu()

            elif self.startGame:
                if len(self.enemies) == 0:
                    current_time = time.get_ticks()
                    if current_time - self.gameTimer < 3000:
                        self.screen.blit(self.background, (0, 0))
                        self.scoreText2 = Text(FONT, 20, str(self.score),
                                               GREEN, 85, 5)
                        self.scoreText.draw(self.screen)
                        self.scoreText2.draw(self.screen)
                        self.nextRoundText.draw(self.screen)
                        self.livesText.draw(self.screen)
                        self.livesGroup.update()
                    if current_time - self.gameTimer > 3000:
                        # Move enemies closer to bottom
                        self.enemyPositionStart += 35
                        self.reset(self.score, len(self.livesGroup))
                        self.gameTimer += 3000
                else:
                    current_time = time.get_ticks()
                    self.play_main_music(current_time)
                    self.screen.blit(self.background, (0, 0))
                    self.allBlockers.update(self.screen)
                    self.scoreText2 = Text(FONT, 20, str(self.score), GREEN,
                                           85, 5)
                    self.scoreText.draw(self.screen)
                    self.scoreText2.draw(self.screen)
                    self.livesText.draw(self.screen)
                    self.check_input()
                    keys = key.get_pressed()
                    self.allSprites.update(keys, current_time, self.enemies)
                    self.explosionsGroup.update(current_time)
                    self.check_collisions()
                    self.create_new_ship(self.makeNewShip, current_time)
                    self.update_enemy_speed()

                    if len(self.enemies) > 0:
                        self.make_enemies_shoot()

            elif self.gameOver:
                current_time = time.get_ticks()
                # Reset enemy start position
                self.enemyPositionStart = self.enemyPositionDefault
                self.create_game_over(current_time)

            display.update()
            self.clock.tick(60)


if __name__ == '__main__':
    game = SpaceInvaders()
    game.main()
