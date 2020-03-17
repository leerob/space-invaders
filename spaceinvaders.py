#!/usr/bin/env python

# Space Invaders
# Created by Lee Robinson
from datetime import datetime, timedelta
from pathlib import Path

import attr
from pygame import *
import sys
from os.path import abspath, dirname
from random import choice

from Bullet import Bullet
from Blocker import Blocker
from bug_reporter import bug_reporter
from consts import *
from Mystery import Mystery, MysteryExplosion
from Ship import Ship, ShipExplosion
from Enemy import Enemy, EnemiesGroup, EnemyExplosion
from UI import Life, Text
from datetime import datetime
import struct

EPOCH = datetime(1970, 1, 1)
RECORDS_PATH = Path("./records.data")


class SpaceInvaders(object):

    @attr.s
    class Record:
        time = attr.ib()
        score = attr.ib()

    def __init__(self):
        # It seems, in Linux buffersize=512 is not enough, use 4096 to prevent:
        #   ALSA lib pcm.c:7963:(snd_pcm_recover) underrun occurred
        mixer.pre_init(44100, -16, 1, 4096)
        init()
        self.clock = time.Clock()
        self.caption = display.set_caption('Space Invaders')
        self.screen = SCREEN
        self.background = image.load(IMAGE_PATH + 'background.jpg').convert()
        self.startGame = False
        self.mainScreen = True
        self.recordsScreen = False
        self.gameOver = False
        # Counter for enemy starting position (increased each new round)
        self.enemyPosition = ENEMY_DEFAULT_POSITION
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

        self.life1 = Life(715, 3)
        self.life2 = Life(742, 3)
        self.life3 = Life(769, 3)
        self.livesGroup = sprite.Group(self.life1, self.life2, self.life3)
        
        self.explosionsGroup = sprite.Group()
        self.bullets = sprite.Group()
        self.mysteryShip = Mystery()
        self.mysteryGroup = sprite.Group(self.mysteryShip)
        self.enemyBullets = sprite.Group()

        self.recordsPath = RECORDS_PATH

    def reset(self, score):
        self.player = Ship()
        self.playerGroup = sprite.Group(self.player)
        self.mysteryShip = Mystery()
        self.mysteryGroup = sprite.Group(self.mysteryShip)
        self.make_enemies()
        self.allSprites = sprite.Group(self.player, self.enemies,
                                       self.livesGroup, self.mysteryShip)
        self.keys = key.get_pressed()

        self.timer = time.get_ticks()
        self.noteTimer = time.get_ticks()
        self.shipTimer = time.get_ticks()
        self.score = score
        self.create_audio()
        self.makeNewShip = False
        self.shipAlive = True

    def make_blockers(self, number):
        blockerGroup = sprite.Group()
        for row in range(4):
            for column in range(9):
                blocker = Blocker(10, GREEN, row, column)
                blocker.rect.x = 50 + (200 * number) + (column * blocker.width)
                blocker.rect.y = BLOCKERS_POSITION + (row * blocker.height)
                blockerGroup.add(blocker)
        return blockerGroup

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

    def play_main_music(self, currentTime):
        if currentTime - self.noteTimer > self.enemies.moveTime:
            self.note = self.musicNotes[self.noteIndex]
            if self.noteIndex < 3:
                self.noteIndex += 1
            else:
                self.noteIndex = 0

            self.note.play()
            self.noteTimer += self.enemies.moveTime

    @staticmethod
    def should_exit(evt):
        # type: (pygame.event.EventType) -> bool
        return evt.type == QUIT or (evt.type == KEYUP and evt.key == K_ESCAPE)

    def check_input(self):
        self.keys = key.get_pressed()
        for e in event.get():
            if self.should_exit(e):
                sys.exit()
            if e.type == KEYDOWN and e.key == K_SPACE:
                num_bullets = (self.score // 1000) + 1
                center = (self.player.rect.x + 23, self.player.rect.y + 5)
                distance = 15
                leftess_x = self.player.rect.x + 23 - (distance * num_bullets // 2)
                rightest_x = self.player.rect.x + 23 + (distance * num_bullets // 2)
                for i in range(0, num_bullets//2):
                    left_bullet = Bullet(leftess_x + (distance * i),
                                    self.player.rect.y + 5, -1,
                                    15, 'laser', 'left_'+str(i))
                    right_bullet = Bullet(rightest_x - (distance * i),
                                    self.player.rect.y + 5, -1,
                                    15, 'laser', 'right_'+str(i))
                    self.bullets.add(left_bullet)
                    self.bullets.add(right_bullet)
                if num_bullets%2 > 0:
                    bullet = Bullet(self.player.rect.x + 23,
                                    self.player.rect.y + 5, -1,
                                    15, 'laser', 'center')
                    self.bullets.add(bullet)
                if 1 == num_bullets:
                    self.sounds['shoot'].play()
                else:
                    self.sounds['shoot2'].play()
                
                self.allSprites.add(self.bullets)                        

    def make_enemies(self):
        enemies = EnemiesGroup(10, 5)
        for row in range(5):
            for column in range(10):
                enemy = Enemy(row, column)
                enemy.rect.x = 157 + (column * 50)
                enemy.rect.y = self.enemyPosition + (row * 45)
                enemies.add(enemy)

        self.enemies = enemies

    def make_enemies_shoot(self):
        if (time.get_ticks() - self.timer) > 700 and self.enemies:
            enemy = self.enemies.random_bottom()
            self.enemyBullets.add(
                Bullet(enemy.rect.x + 14, enemy.rect.y + 20, 1, 5,
                       'enemylaser', 'center'))
            self.allSprites.add(self.enemyBullets)
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
        if self.score > 2550:
            self.score %= 2550
            bug_reporter.report_bug("Buffer overflow", "Did you really think you can get to 3000 points?")
        return score

    def create_main_menu(self):
        self.enemy1 = IMAGES['enemy3_1']
        self.enemy1 = transform.scale(self.enemy1, (40, 40))
        self.enemy2 = IMAGES['enemy2_2']
        self.enemy2 = transform.scale(self.enemy2, (40, 40))
        self.enemy3 = IMAGES['enemy1_2']
        self.enemy3 = transform.scale(self.enemy3, (40, 40))
        self.enemy4 = IMAGES['mystery']
        self.enemy4 = transform.scale(self.enemy4, (80, 40))
        self.screen.blit(self.enemy1, (318, 270))
        self.screen.blit(self.enemy2, (318, 320))
        self.screen.blit(self.enemy3, (318, 370))
        self.screen.blit(self.enemy4, (299, 420))

    def check_collisions(self):
        sprite.groupcollide(self.bullets, self.enemyBullets, True, True)

        for enemy in sprite.groupcollide(self.enemies, self.bullets,
                                         True, True).keys():
            self.sounds['invaderkilled'].play()
            self.calculate_score(enemy.row)
            EnemyExplosion(enemy, self.explosionsGroup)
            self.gameTimer = time.get_ticks()

        for mystery in sprite.groupcollide(self.mysteryGroup, self.bullets,
                                           True, True).keys():
            mystery.mysteryEntered.stop()
            self.sounds['mysterykilled'].play()
            score = self.calculate_score(mystery.row)
            MysteryExplosion(mystery, score, self.explosionsGroup)
            newShip = Mystery()
            self.allSprites.add(newShip)
            self.mysteryGroup.add(newShip)

        for player in sprite.groupcollide(self.playerGroup, self.enemyBullets,
                                          True, True).keys():
            if self.life3.alive():
                self.life3.kill()
            elif self.life2.alive():
                self.life2.kill()
            elif self.life1.alive():
                self.life1.kill()
            else:
                self.gameOver = True
                self.add_to_records(self.score)
                self.startGame = False
            self.sounds['shipexplosion'].play()
            ShipExplosion(player, self.explosionsGroup)
            self.makeNewShip = True
            self.shipTimer = time.get_ticks()
            self.shipAlive = False

        if self.enemies.bottom >= 540:
            sprite.groupcollide(self.enemies, self.playerGroup, True, True)
            if not self.player.alive() or self.enemies.bottom >= 600:
                self.gameOver = True
                self.add_to_records(self.score)
                self.startGame = False

        sprite.groupcollide(self.bullets, self.allBlockers, True, True)
        sprite.groupcollide(self.enemyBullets, self.allBlockers, True, True)
        if self.enemies.bottom >= BLOCKERS_POSITION:
            sprite.groupcollide(self.enemies, self.allBlockers, False, True)

    def create_new_ship(self, createShip, currentTime):
        if createShip and (currentTime - self.shipTimer > 900):
            self.player = Ship()
            self.allSprites.add(self.player)
            self.playerGroup.add(self.player)
            self.makeNewShip = False
            self.shipAlive = True

    def create_records_screen(self, currentTime):
        colors = [GOLD, SILVER, BRONZE] + 7 * [WHITE]
        self.screen.blit(self.background, (0, 0))
        passed = currentTime - self.timer
        if passed < 40000:
            Text(MONO_FONT, 50, 9 * " " + "Records" + 9 * " ", GREEN, 15, 0).draw(self.screen)
            for i, record in enumerate(self.load_records()):
                if i >= 10:
                    break
                date_as_string = record.time.strftime("%d/%m/%Y %H:%M")
                number_of_dots = 25 - len(date_as_string) - len(str(record.score))
                Text(MONO_FONT, 50, date_as_string + number_of_dots * "." + str(record.score), colors[i], 15
                     , 50 * (i + 1)).draw(self.screen)
        else:
            self.mainScreen = True

        for e in event.get():
            if self.should_exit(e):
                sys.exit()

    def create_game_over(self, currentTime):
        self.screen.blit(self.background, (0, 0))
        passed = currentTime - self.timer
        if passed < 750:
            self.gameOverText.draw(self.screen)
        elif 750 < passed < 1500:
            self.screen.blit(self.background, (0, 0))
        elif 1500 < passed < 2250:
            self.gameOverText.draw(self.screen)
        elif 2250 < passed < 2750:
            self.screen.blit(self.background, (0, 0))
        elif passed > 3000:
            self.recordsScreen = True
            self.gameOver = False

        for e in event.get():
            if self.should_exit(e):
                sys.exit()

    def main(self):
        while True:
            if self.mainScreen:
                self.screen.blit(self.background, (0, 0))
                self.titleText.draw(self.screen)
                self.titleText2.draw(self.screen)
                self.enemy1Text.draw(self.screen)
                self.enemy2Text.draw(self.screen)
                self.enemy3Text.draw(self.screen)
                self.enemy4Text.draw(self.screen)
                self.create_main_menu()
                for e in event.get():
                    if self.should_exit(e):
                        sys.exit()
                    if e.type == KEYUP:
                        # Only create blockers on a new game, not a new round
                        self.allBlockers = sprite.Group(self.make_blockers(0),
                                                        self.make_blockers(1),
                                                        self.make_blockers(2),
                                                        self.make_blockers(3))
                        self.livesGroup.add(self.life1, self.life2, self.life3)
                        self.reset(0)
                        self.startGame = True
                        self.mainScreen = False

            elif self.startGame:
                if not self.enemies and not self.explosionsGroup:
                    currentTime = time.get_ticks()
                    if currentTime - self.gameTimer < 3000:
                        self.screen.blit(self.background, (0, 0))
                        self.scoreText2 = Text(FONT, 20, str(self.score),
                                               GREEN, 85, 5)
                        self.scoreText.draw(self.screen)
                        self.scoreText2.draw(self.screen)
                        self.nextRoundText.draw(self.screen)
                        self.livesText.draw(self.screen)
                        self.livesGroup.update()
                        self.check_input()
                    if currentTime - self.gameTimer > 3000:
                        # Move enemies closer to bottom
                        self.enemyPosition += ENEMY_MOVE_DOWN
                        self.reset(self.score)
                        self.gameTimer += 3000
                else:
                    currentTime = time.get_ticks()
                    self.play_main_music(currentTime)
                    self.screen.blit(self.background, (0, 0))
                    self.allBlockers.update(self.screen)
                    self.scoreText2 = Text(FONT, 20, str(self.score), GREEN,
                                           85, 5)
                    self.scoreText.draw(self.screen)
                    self.scoreText2.draw(self.screen)
                    self.livesText.draw(self.screen)
                    self.check_input()
                    self.enemies.update(currentTime)
                    self.allSprites.update(self.keys, currentTime)
                    self.explosionsGroup.update(currentTime)
                    self.check_collisions()
                    self.create_new_ship(self.makeNewShip, currentTime)
                    self.make_enemies_shoot()
                    
                    if self.clock.get_fps() < BASE_FPS//2 and len(self.bullets) > 1000:
                        bug_reporter.report_bug("Stress Test", \
                        "Bullet Hell just caused the frame rate to drop by more than half")


            elif self.gameOver:
                currentTime = time.get_ticks()
                # Reset enemy starting position
                self.enemyPosition = ENEMY_DEFAULT_POSITION
                self.create_game_over(currentTime)

            elif self.recordsScreen:
                currentTime = time.get_ticks()
                self.create_records_screen(currentTime)
            
            display.update()
            self.clock.tick(60)

    def load_records(self):
        if not self.recordsPath.exists():
            return []
        with self.recordsPath.open("rb") as f:
            records = f.readlines()
        parsed_records = []
        for record in records:
            time_since_epoc, score = struct.unpack("II", record[:-1])
            parsed_records.append(SpaceInvaders.Record(EPOCH + timedelta(seconds=time_since_epoc), score))
        return parsed_records

    def add_to_records(self, score):
        current_time = datetime.now()
        records = self.load_records()
        records.append(SpaceInvaders.Record(current_time, score))
        records.sort(key=lambda record: record.score)
        records.reverse()
        self._save_records(records[:10])

    def _save_records(self, records):
        with self.recordsPath.open("wb") as output:
            for record in records:
                time_since_epoc = int((record.time - EPOCH).total_seconds())
                max_int = struct.unpack("I", b"\xFF" * 4)[0]
                if time_since_epoc < 0 or time_since_epoc > max_int:
                    bug_reporter.report_bug("Type 40 bug",
                                            "Is it the past or is it the future??? There's something wrong with time...")
                    # Make sure that the program won't crash
                    time_since_epoc = time_since_epoc % max_int
                    if time_since_epoc < 0:
                        time_since_epoc += max_int

                output.write(struct.pack("II", time_since_epoc, record.score))
                output.write(b"\n")


if __name__ == '__main__':
    game = SpaceInvaders()
    game.main()
