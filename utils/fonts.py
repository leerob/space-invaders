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
import pygame
from utils.parameters import WIDTH_UNIT

pygame.font.init()
GAMEOVER_FONT = pygame.font.Font('data/font/bit5x3.ttf', 10 * WIDTH_UNIT)
CREDIT_FONT = pygame.font.Font('data/font/bit5x3.ttf', 2 * WIDTH_UNIT)
REPLAY_FONT = pygame.font.Font('data/font/bit5x3.ttf', 5 * WIDTH_UNIT)
SCORE_FONT = pygame.font.Font('data/font/bit5x3.ttf', 12 * WIDTH_UNIT)
VECTOR_FONT = pygame.font.Font('data/font/bit5x3.ttf', 3 * WIDTH_UNIT)
PLAYER_FONT = pygame.font.Font('data/font/bit5x3.ttf', 3 * WIDTH_UNIT)
