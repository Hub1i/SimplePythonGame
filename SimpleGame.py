import pygame
import math
import random
import numpy as np
import asyncio
import platform
from collections import deque
from dataclasses import dataclass
from typing import List, Tuple

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
TILE_SIZE = 32
MAP_WIDTH = 50
MAP_HEIGHT = 50
MAX_ENEMIES = 8
PARTICLE_LIFETIME = 20
CHEST_SPAWN_RATE = 0.002

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (100, 100, 100)
YELLOW = (255, 255, 0)
DARK_GRAY = (50, 50, 50)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Survivor")
clock = pygame.time.Clock()
font = pygame.font.SysFont('arial', 20)
title_font = pygame.font.SysFont('arial', 40)

# Sprites
player_sprite = pygame.Surface((20, 20))
player_sprite.fill(GREEN)
enemy_drone_sprite = pygame.Surface((30, 30))
enemy_drone_sprite.fill(RED)
enemy_tank_sprite = pygame.Surface((30, 30))
enemy_tank_sprite.fill(YELLOW)
boss_sprite = pygame.Surface((50, 50))
boss_sprite.fill(CYAN)
item_sprite = pygame.Surface((10, 10))
item_sprite.fill(BLUE)
chest_sprite = pygame.Surface((20, 20))
chest_sprite.fill(PURPLE)
health_sprite = pygame.Surface((10, 10))
health_sprite.fill(ORANGE)

@dataclass
class Particle:
    pos: Tuple[float, float]
    vel: Tuple[float, float]
    color: Tuple[int, int, int]
    lifetime: int
    size: float

@dataclass
class Bullet:
    pos: Tuple[float, float]
    vel: Tuple[float, float]
    damage: int
    owner: str
    spread: float = 0.0

@dataclass
class Item:
    name: str
    type: str
    value: int
    pos: Tuple[float, float]
    stats: dict = None

@dataclass
class Chest:
    pos: Tuple[float, float]
    contents: List[Item]

@dataclass
class Weapon:
    name: str
    damage: int
    fire_rate: int
    speed: float
    spread: float
    bullet_count: int = 1
    ammo: int = -1
    max_ammo: int = -1

class Inventory:
    def __init__(self):
        self.items: List[Item] = []
        self.capacity = 20
        self.weapons = [Weapon("Pistol", 10, 10, 10, 0.0, 1, -1, -1)]
        self.selected_weapon = 0
        self.ammo = {"Pistol": -1}

    def add_item(self, item: Item) -> bool:
        if len(self.items) < self.capacity:
            self.items.append(item)
            if item.type == "weapon":
                self.weapons.append(item.stats)
                self.ammo[item.stats.name] = item.stats.max_ammo
            return True
        return False

    def get_weapon(self) -> Weapon:
        return self.weapons[self.selected_weapon]

    def use_ammo(self, weapon_name: str) -> bool:
        if self.ammo.get(weapon_name, -1) == -1:
            return True
        if self.ammo[weapon_name] > 0:
            self.ammo[weapon_name] -= 1
            return True
        return False

class Player:
    def __init__(self, x: float, y: float):
        self.pos = [x, y]
        self.vel = [0, 0]
        self.speed = 5
        self.health = 100
        self.max_health = 100
        self.level = 1
        self.exp = 0
        self.exp_to_next = 100
        self.resources = 0
        self.inventory = Inventory()
        self.fire_timer = 0
        self.damage_modifier = 1.0
        self.armor = 0
        self.regen_timer = 0
        self.regen_rate = 0
        self.temp_health_boost = 0
        self.temp_health_timer = 0

    def move(self, keys: pygame.key.ScancodeWrapper, walls: List[pygame.Rect]):
        self.vel = [0, 0]
        if keys[pygame.K_w]:
            self.vel[1] = -self.speed
        if keys[pygame.K_s]:
            self.vel[1] = self.speed
        if keys[pygame.K_a]:
            self.vel[0] = -self.speed
        if keys[pygame.K_d]:
            self.vel[0] = self.speed

        if self.vel[0] != 0 and self.vel[1] != 0:
            self.vel[0] *= 0.707
            self.vel[1] *= 0.707

        new_rect = pygame.Rect(self.pos[0] + self.vel[0], self.pos[1], 20, 20)
        if not any(new_rect.colliderect(wall) for wall in walls):
            self.pos[0] += self.vel[0]
        new_rect = pygame.Rect(self.pos[0], self.pos[1] + self.vel[1], 20, 20)
        if not any(new_rect.colliderect(wall) for wall in walls):
            self.pos[1] += self.vel[1]

    def shoot(self, mouse_pos: Tuple[int, int]) -> List[Bullet]:
        weapon = self.inventory.get_weapon()
        if not self.inventory.use_ammo(weapon.name):
            return []
        bullets = []
        dx = mouse_pos[0] - (self.pos[0] - camera.offset[0])
        dy = mouse_pos[1] - (self.pos[1] - camera.offset[1])
        angle = math.atan2(dy, dx)
        for _ in range(weapon.bullet_count):
            spread = random.uniform(-weapon.spread, weapon.spread)
            bullets.append(Bullet(
                pos=(self.pos[0], self.pos[1]),
                vel=(math.cos(angle + spread) * weapon.speed, math.sin(angle + spread) * weapon.speed),
                damage=int(weapon.damage * self.damage_modifier),
                owner='player',
                spread=weapon.spread
            ))
        return bullets

    def gain_exp(self, amount: int):
        self.exp += amount
        while self.exp >= self.exp_to_next:
            self.level_up()

    def level_up(self):
        global upgrade_menu_active, boss_active
        self.level += 1
        self.exp -= self.exp_to_next
        self.exp_to_next = int(self.exp_to_next * 1.5)
        self.max_health += 20
        self.health = min(self.health + 20, self.max_health + self.temp_health_boost)
        if self.level % 5 == 0 and not boss_active:
            spawn_boss()
            boss_active = True
        else:
            upgrade_menu_active = True
            global upgrade_options
            upgrade_options = self.get_upgrade_options()

    def get_upgrade_options(self) -> List[dict]:
        options = [
            {"name": "Damage +20%", "effect": lambda: setattr(self, "damage_modifier", self.damage_modifier + 0.2)},
            {"name": "Speed +10%", "effect": lambda: setattr(self, "speed", self.speed * 1.1)},
            {"name": "Armor +3", "effect": lambda: setattr(self, "armor", self.armor + 3)},
            {"name": "Health Regen +1/s", "effect": lambda: setattr(self, "regen_rate", self.regen_rate + 1)},
            {"name": "Max Health +20", "effect": lambda: setattr(self, "max_health", self.max_health + 20) or setattr(self, "health", min(self.health + 20, self.max_health + self.temp_health_boost))},
        ]
        return random.sample(options, min(3, len(options)))

    def apply_item(self, item: Item):
        if item.type == "health":
            self.health = min(self.health + item.value, self.max_health + self.temp_health_boost)
        elif item.type == "temp_health":
            self.temp_health_boost += item.value
            self.temp_health_timer = item.stats["duration"]
        elif item.type == "armor":
            self.armor += item.value
        elif item.type == "ammo":
            self.inventory.ammo[item.stats["weapon"]] = min(
                self.inventory.ammo.get(item.stats["weapon"], 0) + item.value,
                item.stats["max_ammo"]
            )

    def update(self):
        if self.regen_timer <= 0 and self.regen_rate > 0:
            self.health = min(self.health + self.regen_rate, self.max_health + self.temp_health_boost)
            self.regen_timer = 60
        else:
            self.regen_timer -= 1

        if self.temp_health_timer > 0:
            self.temp_health_timer -= 1
            if self.temp_health_timer <= 0:
                self.temp_health_boost = 0
                self.health = min(self.health, self.max_health)

    def take_damage(self, amount: int):
        actual_damage = max(1, amount - self.armor)
        self.health -= actual_damage
        if self.health < 0:
            self.health = 0

class Enemy:
    def __init__(self, x: float, y: float, type: str):
        self.pos = [x, y]
        self.type = type
        self.health = 80 if type == 'drone' else 150
        self.max_health = self.health
        self.speed = 2.5 if type == 'drone' else 1.8
        self.damage = 10 if type == 'drone' else 20
        self.fire_rate = 60 if type == 'drone' else 90
        self.fire_timer = random.randint(0, self.fire_rate)
        self.path = []
        self.path_timer = 0
        self.behavior = 'ranged' if type == 'drone' else 'charge'

    def move_toward(self, target_pos: Tuple[float, float], walls: List[pygame.Rect]):
        self.path_timer -= 1
        if (not self.path or self.path_timer <= 0) and random.random() < 0.05:
            self.path = a_star(self.pos, target_pos, walls)
            self.path_timer = 30
        if self.path:
            next_pos = self.path[0]
            dx = next_pos[0] * TILE_SIZE + TILE_SIZE // 2 - self.pos[0]
            dy = next_pos[1] * TILE_SIZE + TILE_SIZE // 2 - self.pos[1]
            dist = math.hypot(dx, dy)
            if dist > 5:
                self.pos[0] += (dx / dist) * self.speed
                self.pos[1] += (dy / dist) * self.speed
            else:
                self.path.pop(0)
        elif self.behavior == 'charge':
            dx = target_pos[0] - self.pos[0]
            dy = target_pos[1] - self.pos[1]
            dist = max(math.hypot(dx, dy), 1)
            self.pos[0] += (dx / dist) * self.speed
            self.pos[1] += (dy / dist) * self.speed

    def shoot(self, target_pos: Tuple[float, float]) -> Bullet:
        dx = target_pos[0] - self.pos[0]
        dy = target_pos[1] - self.pos[1]
        angle = math.atan2(dy, dx)
        speed = 8
        return Bullet(
            pos=(self.pos[0], self.pos[1]),
            vel=(math.cos(angle) * speed, math.sin(angle) * speed),
            damage=self.damage,
            owner='enemy'
        )

    def take_damage(self, amount: int):
        self.health -= amount
        if self.health <= 0:
            return True
        return False

class Boss:
    def __init__(self, x: float, y: float):
        self.pos = [x, y]
        self.health = 500 + player.level * 100
        self.max_health = self.health
        self.speed = 1.5
        self.damage = 30
        self.fire_rate = 30
        self.fire_timer = 0
        self.path = []
        self.path_timer = 0
        self.attack_phase = 0

    def move_toward(self, target_pos: Tuple[float, float], walls: List[pygame.Rect]):
        self.path_timer -= 1
        if (not self.path or self.path_timer <= 0) and random.random() < 0.1:
            self.path = a_star(self.pos, target_pos, walls)
            self.path_timer = 20
        if self.path:
            next_pos = self.path[0]
            dx = next_pos[0] * TILE_SIZE + TILE_SIZE // 2 - self.pos[0]
            dy = next_pos[1] * TILE_SIZE + TILE_SIZE // 2 - self.pos[1]
            dist = math.hypot(dx, dy)
            if dist > 5:
                self.pos[0] += (dx / dist) * self.speed
                self.pos[1] += (dy / dist) * self.speed
            else:
                self.path.pop(0)

    def shoot(self, target_pos: Tuple[float, float]) -> List[Bullet]:
        bullets = []
        dx = target_pos[0] - self.pos[0]
        dy = target_pos[1] - self.pos[1]
        angle = math.atan2(dy, dx)
        if self.attack_phase == 0:
            for i in range(-2, 3):
                bullets.append(Bullet(
                    pos=(self.pos[0], self.pos[1]),
                    vel=(math.cos(angle + i * 0.2) * 6, math.sin(angle + i * 0.2) * 6),
                    damage=self.damage,
                    owner='boss'
                ))
        else:
            bullets.append(Bullet(
                pos=(self.pos[0], self.pos[1]),
                vel=(math.cos(angle) * 10, math.sin(angle) * 10),
                damage=self.damage // 2,
                owner='boss'
            ))
        self.attack_phase = (self.attack_phase + 1) % 2
        return bullets

    def take_damage(self, amount: int):
        self.health -= amount
        if self.health <= 0:
            return True
        return False

class Camera:
    def __init__(self):
        self.offset = [0, 0]

    def update(self, target_pos: Tuple[float, float]):
        self.offset[0] = target_pos[0] - SCREEN_WIDTH // 2
        self.offset[1] = target_pos[1] - SCREEN_HEIGHT // 2

class Map:
    def __init__(self):
        self.tiles = [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        self.generate_map()

    def generate_map(self):
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if random.random() < 0.15:
                    self.tiles[y][x] = 1
                else:
                    self.tiles[y][x] = 0
        self.tiles[MAP_HEIGHT // 2][MAP_WIDTH // 2] = 0

    def get_walls(self) -> List[pygame.Rect]:
        walls = []
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if self.tiles[y][x] == 1:
                    walls.append(pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        return walls

    def draw(self, surface: pygame.Surface, camera: Camera):
        surface.fill(DARK_GRAY)
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                screen_x = x * TILE_SIZE - camera.offset[0]
                screen_y = y * TILE_SIZE - camera.offset[1]
                if -TILE_SIZE <= screen_x < SCREEN_WIDTH + TILE_SIZE and -TILE_SIZE <= screen_y < SCREEN_HEIGHT + TILE_SIZE:
                    color = GRAY if self.tiles[y][x] == 1 else BLACK
                    pygame.draw.rect(surface, color, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))

def a_star(start: Tuple[float, float], goal: Tuple[float, float], walls: List[pygame.Rect]) -> List[Tuple[int, int]]:
    start_node = (int(start[0] // TILE_SIZE), int(start[1] // TILE_SIZE))
    goal_node = (int(goal[0] // TILE_SIZE), int(goal[1] // TILE_SIZE))
    open_set = {start_node}
    closed_set = set()
    came_from = {}
    g_score = {start_node: 0}
    f_score = {start_node: math.hypot(start_node[0] - goal_node[0], start_node[1] - goal_node[1])}

    while open_set:
        current = min(open_set, key=lambda node: f_score.get(node, float('inf')))
        if current == goal_node:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            return path[::-1][:10]

        open_set.remove(current)
        closed_set.add(current)

        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            neighbor = (current[0] + dx, current[1] + dy)
            if 0 <= neighbor[0] < MAP_WIDTH and 0 <= neighbor[1] < MAP_HEIGHT:
                neighbor_rect = pygame.Rect(neighbor[0] * TILE_SIZE, neighbor[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if any(neighbor_rect.colliderect(wall) for wall in walls):
                    continue
                if neighbor in closed_set:
                    continue
                tentative_g_score = g_score[current] + 1.0
                if neighbor not in open_set:
                    open_set.add(neighbor)
                elif tentative_g_score >= g_score.get(neighbor, float('inf')):
                    continue
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + math.hypot(neighbor[0] - goal_node[0], neighbor[1] - goal_node[1])

    return []

def generate_explosion_sound():
    sample_rate = 44100
    duration = 0.2
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    noise = np.random.normal(0, 0.5, t.shape)
    envelope = np.exp(-5 * t / duration)
    sound_data = (noise * envelope * 32767).astype(np.int16)
    sound_array = np.column_stack((sound_data, sound_data))
    sound = pygame.sndarray.make_sound(sound_array)
    return sound

def generate_shot_sound():
    sample_rate = 44100
    duration = 0.1
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    freq = 440
    wave = np.sin(2 * np.pi * freq * t)
    envelope = np.exp(-10 * t / duration)
    sound_data = (wave * envelope * 32767).astype(np.int16)
    sound_array = np.column_stack((sound_data, sound_data))
    sound = pygame.sndarray.make_sound(sound_array)
    return sound

def generate_pickup_sound():
    sample_rate = 44100
    duration = 0.1
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    freq = 880
    wave = np.sin(2 * np.pi * freq * t)
    envelope = np.exp(-10 * t / duration)
    sound_data = (wave * envelope * 32767).astype(np.int16)
    sound_array = np.column_stack((sound_data, sound_data))
    sound = pygame.sndarray.make_sound(sound_array)
    return sound

# Sound effects
explosion_sound = generate_explosion_sound()
shot_sound = generate_shot_sound()
pickup_sound = generate_pickup_sound()

# Game state
player = Player(MAP_WIDTH * TILE_SIZE // 2, MAP_HEIGHT * TILE_SIZE // 2)
enemies = []
bullets = []
particles = []
items = []
chests = []
boss = None
camera = Camera()
game_map = Map()
walls = game_map.get_walls()
running = True
game_over = False
title_screen = True
upgrade_menu_active = False
upgrade_options = []
selected_upgrade = 0
paused = False
pause_selection = 0
boss_active = False

def spawn_enemy():
    while len(enemies) < MAX_ENEMIES and not boss_active:
        x = random.randint(0, MAP_WIDTH - 1) * TILE_SIZE + TILE_SIZE // 2
        y = random.randint(0, MAP_HEIGHT - 1) * TILE_SIZE + TILE_SIZE // 2
        enemy_rect = pygame.Rect(x - 15, y - 15, 30, 30)
        if not any(enemy_rect.colliderect(wall) for wall in walls) and math.hypot(x - player.pos[0], y - player.pos[1]) > 300:
            enemy_type = random.choice(['drone', 'tank'])
            enemy = Enemy(x, y, enemy_type)
            enemy.health += player.level * 20
            enemy.max_health = enemy.health
            enemies.append(enemy)

def spawn_boss():
    global boss, enemies
    enemies = []
    x = random.randint(0, MAP_WIDTH - 1) * TILE_SIZE + TILE_SIZE // 2
    y = random.randint(0, MAP_HEIGHT - 1) * TILE_SIZE + TILE_SIZE // 2
    boss_rect = pygame.Rect(x - 25, y - 25, 50, 50)
    while any(boss_rect.colliderect(wall) for wall in walls) or math.hypot(x - player.pos[0], y - player.pos[1]) < 500:
        x = random.randint(0, MAP_WIDTH - 1) * TILE_SIZE + TILE_SIZE // 2
        y = random.randint(0, MAP_HEIGHT - 1) * TILE_SIZE + TILE_SIZE // 2
        boss_rect = pygame.Rect(x - 25, y - 25, 50, 50)
    boss = Boss(x, y)

def spawn_item(pos: Tuple[float, float]):
    item_types = [
        Item('Health Pack', 'health', 50, pos),
        Item('Temp Health Boost', 'temp_health', 50, pos, {"duration": 600}),
        Item('Armor', 'armor', 5, pos),
        Item('Resource', 'resource', 2, pos),
        Item('Shotgun Ammo', 'ammo', 20, pos, {"weapon": "Shotgun", "max_ammo": 100}),
        Item('Sniper Ammo', 'ammo', 10, pos, {"weapon": "Sniper", "max_ammo": 50}),
        Item('Laser Ammo', 'ammo', 30, pos, {"weapon": "Laser", "max_ammo": 150}),
        Item('Grenade Ammo', 'ammo', 5, pos, {"weapon": "Grenade Launcher", "max_ammo": 20}),
        Item('Flamethrower Ammo', 'ammo', 50, pos, {"weapon": "Flamethrower", "max_ammo": 200}),
        Item('Plasma Ammo', 'ammo', 15, pos, {"weapon": "Plasma Rifle", "max_ammo": 80}),
        Item('Rocket Ammo', 'ammo', 5, pos, {"weapon": "Rocket Launcher", "max_ammo": 15}),
        Item('Freeze Ammo', 'ammo', 10, pos, {"weapon": "Freeze Shotgun", "max_ammo": 60}),
    ]
    items.append(random.choice(item_types))

def spawn_chest():
    x = random.randint(0, MAP_WIDTH - 1) * TILE_SIZE + TILE_SIZE // 2
    y = random.randint(0, MAP_HEIGHT - 1) * TILE_SIZE + TILE_SIZE // 2
    chest_rect = pygame.Rect(x - 10, y - 10, 20, 20)
    if not any(chest_rect.colliderect(wall) for wall in walls) and math.hypot(x - player.pos[0], y - player.pos[1]) > 200:
        weapon_types = [
            Item('Shotgun', 'weapon', 0, (x, y), Weapon('Shotgun', 30, 20, 8, 0.2, 5, 50, 100)),
            Item('Sniper', 'weapon', 0, (x, y), Weapon('Sniper', 50, 30, 12, 0.0, 1, 20, 50)),
            Item('Laser', 'weapon', 0, (x, y), Weapon('Laser', 15, 5, 15, 0.0, 1, 100, 150)),
            Item('Grenade Launcher', 'weapon', 0, (x, y), Weapon('Grenade Launcher', 80, 60, 6, 0.3, 1, 10, 20)),
            Item('Flamethrower', 'weapon', 0, (x, y), Weapon('Flamethrower', 5, 3, 10, 0.4, 3, 150, 200)),
            Item('Plasma Rifle', 'weapon', 0, (x, y), Weapon('Plasma Rifle', 25, 15, 10, 0.1, 2, 40, 80)),
            Item('Rocket Launcher', 'weapon', 0, (x, y), Weapon('Rocket Launcher', 100, 90, 5, 0.4, 1, 8, 15)),
            Item('Freeze Shotgun', 'weapon', 0, (x, y), Weapon('Freeze Shotgun', 20, 25, 7, 0.25, 6, 30, 60)),
        ]
        contents = random.sample([
            Item('Health Pack', 'health', 50, (x, y)),
            Item('Temp Health Boost', 'temp_health', 50, (x, y), {"duration": 600}),
            Item('Armor', 'armor', 5, (x, y)),
            *weapon_types
        ], k=random.randint(1, 3))
        chests.append(Chest(pos=(x, y), contents=contents))

def create_explosion(pos: Tuple[float, float]):
    for _ in range(10):
        angle = random.random() * 2 * math.pi
        speed = random.random() * 4
        vel = (math.cos(angle) * speed, math.sin(angle) * speed)
        color = random.choice([RED, YELLOW, WHITE])
        size = random.uniform(2, 4)
        particles.append(Particle(pos, vel, color, PARTICLE_LIFETIME, size))
    explosion_sound.play()

def draw_hud(surface: pygame.Surface):
    pygame.draw.rect(surface, BLACK, (10, 10, 104, 24), 2)
    health_width = (player.health / (player.max_health + player.temp_health_boost)) * 100
    pygame.draw.rect(surface, GREEN, (12, 12, health_width, 20))
    
    resource_text = font.render(f'Resources: {player.resources}/100', True, WHITE)
    level_text = font.render(f'Level: {player.level} (EXP: {player.exp}/{player.exp_to_next})', True, WHITE)
    surface.blit(resource_text, (10, 40))
    surface.blit(level_text, (10, 60))
    
    weapon = player.inventory.get_weapon()
    ammo_text = font.render(f'Weapon: {weapon.name} (DMG: {weapon.damage}, Ammo: {player.inventory.ammo.get(weapon.name, "∞")})', True, WHITE)
    surface.blit(ammo_text, (10, 80))
    
    inventory_text = font.render('Inventory:', True, WHITE)
    surface.blit(inventory_text, (SCREEN_WIDTH - 150, 10))
    for i, item in enumerate(player.inventory.items):
        item_text = font.render(f'{item.name} ({item.type})', True, WHITE)
        surface.blit(item_text, (SCREEN_WIDTH - 150, 30 + i * 20))
    
    minimap_size = 100
    minimap = pygame.Surface((minimap_size, minimap_size))
    minimap.fill(BLACK)
    scale = minimap_size / (MAP_WIDTH * TILE_SIZE)
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if game_map.tiles[y][x] == 1:
                pygame.draw.rect(minimap, GRAY, (x * scale * TILE_SIZE, y * scale * TILE_SIZE, scale * TILE_SIZE, scale * TILE_SIZE))
    pygame.draw.rect(minimap, GREEN, (player.pos[0] * scale - 2, player.pos[1] * scale - 2, 4, 4))
    for enemy in enemies:
        pygame.draw.rect(minimap, RED, (enemy.pos[0] * scale - 2, enemy.pos[1] * scale - 2, 4, 4))
    for chest in chests:
        pygame.draw.rect(minimap, PURPLE, (chest.pos[0] * scale - 2, chest.pos[1] * scale - 2, 4, 4))
    if boss:
        pygame.draw.rect(minimap, CYAN, (boss.pos[0] * scale - 2, boss.pos[1] * scale - 2, 4, 4))
    surface.blit(minimap, (SCREEN_WIDTH - minimap_size - 10, SCREEN_HEIGHT - minimap_size - 10))

def draw_title_screen(surface: pygame.Surface):
    surface.fill(BLACK)
    title = title_font.render("Space Survivor", True, WHITE)
    story = font.render("You are the last survivor on a derelict space station.", True, WHITE)
    story2 = font.render("Fight enemies, collect resources, and defeat the Core.", True, WHITE)
    controls = font.render("WASD: Move | Mouse: Aim/Shoot | E: Items | Q: Chests | 1-3/Scroll: Switch Weapon | ESC: Pause", True, WHITE)
    start = font.render("Press SPACE to start", True, WHITE)
    surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))
    surface.blit(story, (SCREEN_WIDTH // 2 - story.get_width() // 2, 200))
    surface.blit(story2, (SCREEN_WIDTH // 2 - story2.get_width() // 2, 230))
    surface.blit(controls, (SCREEN_WIDTH // 2 - controls.get_width() // 2, 300))
    surface.blit(start, (SCREEN_WIDTH // 2 - start.get_width() // 2, 400))

def draw_upgrade_menu(surface: pygame.Surface):
    surface.fill(BLACK)
    title = title_font.render("Choose an Upgrade", True, WHITE)
    surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))
    for i, option in enumerate(upgrade_options):
        color = YELLOW if i == selected_upgrade else WHITE
        text = font.render(option["name"], True, color)
        surface.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 200 + i * 40))
    prompt = font.render("Use UP/DOWN to select, ENTER to confirm", True, WHITE)
    surface.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 400))

def draw_pause_menu(surface: pygame.Surface):
    surface.fill(BLACK)
    title = title_font.render("Paused", True, WHITE)
    options = ["Continue", "Exit"]
    surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 200))
    for i, option in enumerate(options):
        color = YELLOW if i == pause_selection else WHITE
        text = font.render(option, True, color)
        surface.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 300 + i * 40))
    prompt = font.render("Use UP/DOWN to select, ENTER to confirm", True, WHITE)
    surface.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 400))

def setup():
    player.inventory.add_item(Item('Pistol', 'weapon', 0, (0, 0), Weapon('Pistol', 10, 10, 10, 0.0, 1, -1, -1)))
    spawn_enemy()
    spawn_chest()

async def update_loop():
    global running, game_over, title_screen, player, enemies, bullets, particles, items, walls, chests, upgrade_menu_active, selected_upgrade, paused, pause_selection, boss, boss_active
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = not paused
                    pause_selection = 0
                elif title_screen and event.key == pygame.K_SPACE:
                    title_screen = False
                    setup()
                elif paused:
                    if event.key == pygame.K_UP:
                        pause_selection = (pause_selection - 1) % 2
                    elif event.key == pygame.K_DOWN:
                        pause_selection = (pause_selection + 1) % 2
                    elif event.key == pygame.K_RETURN:
                        if pause_selection == 0:
                            paused = False
                        else:
                            running = False
                elif upgrade_menu_active:
                    if event.key == pygame.K_UP:
                        selected_upgrade = (selected_upgrade - 1) % len(upgrade_options)
                    elif event.key == pygame.K_DOWN:
                        selected_upgrade = (selected_upgrade + 1) % len(upgrade_options)
                    elif event.key == pygame.K_RETURN:
                        upgrade_options[selected_upgrade]["effect"]()
                        upgrade_menu_active = False
                        selected_upgrade = 0
                elif event.key == pygame.K_e:
                    player_rect = pygame.Rect(player.pos[0] - 10, player.pos[1] - 10, 20, 20)
                    for item in items[:]:
                        item_rect = pygame.Rect(item.pos[0] - 10, item.pos[1] - 10, 20, 20)
                        if player_rect.colliderect(item_rect):
                            if item.type in ["health", "temp_health", "armor", "ammo"]:
                                player.apply_item(item)
                            elif player.inventory.add_item(item):
                                items.remove(item)
                                pickup_sound.play()
                elif event.key == pygame.K_q:
                    player_rect = pygame.Rect(player.pos[0] - 10, player.pos[1] - 10, 20, 20)
                    for chest in chests[:]:
                        chest_rect = pygame.Rect(chest.pos[0] - 10, chest.pos[1] - 10, 20, 20)
                        if player_rect.colliderect(chest_rect):
                            for item in chest.contents:
                                if item.type in ["health", "temp_health", "armor", "ammo"]:
                                    player.apply_item(item)
                                elif player.inventory.add_item(item):
                                    pickup_sound.play()
                            chests.remove(chest)
                            create_explosion(chest.pos)
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    idx = event.key - pygame.K_1
                    if idx < len(player.inventory.weapons):
                        player.inventory.selected_weapon = idx
            elif event.type == pygame.MOUSEWHEEL:
                if not (title_screen or paused or upgrade_menu_active):
                    if event.y > 0:
                        player.inventory.selected_weapon = (player.inventory.selected_weapon - 1) % len(player.inventory.weapons)
                    elif event.y < 0:
                        player.inventory.selected_weapon = (player.inventory.selected_weapon + 1) % len(player.inventory.weapons)

        if title_screen:
            draw_title_screen(screen)
            pygame.display.flip()
            await asyncio.sleep(1.0 / FPS)
            continue

        if paused:
            draw_pause_menu(screen)
            pygame.display.flip()
            await asyncio.sleep(1.0 / FPS)
            continue

        if upgrade_menu_active:
            draw_upgrade_menu(screen)
            pygame.display.flip()
            await asyncio.sleep(1.0 / FPS)
            continue

        if game_over:
            game_over_text = font.render('Game Over! Press R to Restart', True, WHITE)
            screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
            pygame.display.flip()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                player = Player(MAP_WIDTH * TILE_SIZE // 2, MAP_HEIGHT * TILE_SIZE // 2)
                enemies = []
                bullets = []
                particles = []
                items = []
                chests = []
                boss = None
                boss_active = False
                game_map.generate_map()
                walls = game_map.get_walls()
                setup()
                game_over = False
            await asyncio.sleep(1.0 / FPS)
            continue

        # Update player
        player.update()
        keys = pygame.key.get_pressed()
        player.move(keys, walls)
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0] and player.fire_timer <= 0:
            bullets.extend(player.shoot(pygame.mouse.get_pos()))
            player.fire_timer = player.inventory.get_weapon().fire_rate
            if bullets:
                shot_sound.play()
        if player.fire_timer > 0:
            player.fire_timer -= 1

        # Update camera
        camera.update(player.pos)

        # Update enemies
        for enemy in enemies[:]:
            if enemy.behavior == 'ranged':
                dist = math.hypot(enemy.pos[0] - player.pos[0], enemy.pos[1] - player.pos[1])
                if dist > 200:
                    enemy.move_toward(player.pos, walls)
                if enemy.fire_timer <= 0 and dist < 400:
                    bullets.append(enemy.shoot(player.pos))
                    enemy.fire_timer = enemy.fire_rate
                else:
                    enemy.fire_timer -= 1
            else:
                enemy.move_toward(player.pos, walls)

        # Update boss
        if boss:
            dist = math.hypot(boss.pos[0] - player.pos[0], boss.pos[1] - player.pos[1])
            boss.move_toward(player.pos, walls)
            if boss.fire_timer <= 0 and dist < 500:
                bullets.extend(boss.shoot(player.pos))
                boss.fire_timer = boss.fire_rate
            else:
                boss.fire_timer -= 1

        # Update bullets
        for bullet in bullets[:]:
            bullet.pos = (bullet.pos[0] + bullet.vel[0], bullet.pos[1] + bullet.vel[1])
            bullet_rect = pygame.Rect(bullet.pos[0] - 5, bullet.pos[1] - 5, 10, 10)
            if any(bullet_rect.colliderect(wall) for wall in walls):
                bullets.remove(bullet)
                create_explosion(bullet.pos)
                continue
            if bullet.owner == 'player':
                for enemy in enemies[:]:
                    enemy_rect = pygame.Rect(enemy.pos[0] - 15, enemy.pos[1] - 15, 30, 30)
                    if bullet_rect.colliderect(enemy_rect):
                        if enemy.take_damage(bullet.damage):
                            enemies.remove(enemy)
                            player.gain_exp(50 + player.level * 10 if enemy.type == 'drone' else 100 + player.level * 20)
                            create_explosion(enemy.pos)
                            if random.random() < 0.5:
                                spawn_item(enemy.pos)
                        bullets.remove(bullet)
                        break
                if boss:
                    boss_rect = pygame.Rect(boss.pos[0] - 25, boss.pos[1] - 25, 50, 50)
                    if bullet_rect.colliderect(boss_rect):
                        if boss.take_damage(bullet.damage):
                            boss_active = False
                            player.gain_exp(500 + player.level * 100)
                            create_explosion(boss.pos)
                            spawn_chest()
                            spawn_chest()
                            boss = None
                        bullets.remove(bullet)
            elif bullet.owner in ['enemy', 'boss']:
                player_rect = pygame.Rect(player.pos[0] - 10, player.pos[1] - 10, 20, 20)
                if bullet_rect.colliderect(player_rect):
                    player.take_damage(bullet.damage)
                    bullets.remove(bullet)
                    if player.health <= 0:
                        game_over = True

        # Update particles
        for particle in particles[:]:
            particle.pos = (particle.pos[0] + particle.vel[0], particle.pos[1] + particle.vel[1])
            particle.lifetime -= 1
            particle.size *= 0.95
            if particle.lifetime <= 0:
                particles.remove(particle)

        # Spawn new enemies and chests
        if random.random() < 0.005:
            spawn_enemy()
        if random.random() < CHEST_SPAWN_RATE:
            spawn_chest()

        # Draw everything
        game_map.draw(screen, camera)
        
        # Draw items
        for item in items:
            screen_pos = (item.pos[0] - camera.offset[0], item.pos[1] - camera.offset[1])
            sprite = health_sprite if item.type in ["health", "temp_health"] else item_sprite
            screen.blit(sprite, (screen_pos[0] - 5, screen_pos[1] - 5))
        
        # Draw chests
        for chest in chests:
            screen_pos = (chest.pos[0] - camera.offset[0], chest.pos[1] - camera.offset[1])
            screen.blit(chest_sprite, (screen_pos[0] - 10, screen_pos[1] - 10))
        
        # Draw player
        screen_pos = (player.pos[0] - camera.offset[0], player.pos[1] - camera.offset[1])
        screen.blit(player_sprite, (screen_pos[0] - 10, screen_pos[1] - 10))
        
        # Draw enemies
        for enemy in enemies:
            screen_pos = (enemy.pos[0] - camera.offset[0], enemy.pos[1] - camera.offset[1])
            sprite = enemy_drone_sprite if enemy.type == 'drone' else enemy_tank_sprite
            screen.blit(sprite, (screen_pos[0] - 15, screen_pos[1] - 15))
            health_width = (enemy.health / enemy.max_health) * 20
            pygame.draw.rect(screen, RED, (screen_pos[0] - 10, screen_pos[1] - 25, 20, 5))
            pygame.draw.rect(screen, GREEN, (screen_pos[0] - 10, screen_pos[1] - 25, health_width, 5))
        
        # Draw boss
        if boss:
            screen_pos = (boss.pos[0] - camera.offset[0], boss.pos[1] - camera.offset[1])
            screen.blit(boss_sprite, (screen_pos[0] - 25, screen_pos[1] - 25))
            health_width = (boss.health / boss.max_health) * 40
            pygame.draw.rect(screen, RED, (screen_pos[0] - 20, screen_pos[1] - 35, 40, 5))
            pygame.draw.rect(screen, GREEN, (screen_pos[0] - 20, screen_pos[1] - 35, health_width, 5))
        
        # Draw bullets
        for bullet in bullets:
            screen_pos = (bullet.pos[0] - camera.offset[0], bullet.pos[1] - camera.offset[1])
            pygame.draw.circle(screen, WHITE, screen_pos, 3)
        
        # Draw particles
        for particle in particles:
            screen_pos = (particle.pos[0] - camera.offset[0], particle.pos[1] - camera.offset[1])
            pygame.draw.circle(screen, particle.color, screen_pos, int(particle.size))
        
        # Draw aim line
        mouse_pos = pygame.mouse.get_pos()
        dx = mouse_pos[0] - screen_pos[0]
        dy = mouse_pos[1] - screen_pos[1]
        angle = math.atan2(dy, dx)
        end_pos = (screen_pos[0] + math.cos(angle) * 50, screen_pos[1] + math.sin(angle) * 50)
        pygame.draw.line(screen, WHITE, screen_pos, end_pos, 1)
        
        # Draw HUD
        draw_hud(screen)
        
        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(update_loop())
else:
    if __name__ == "__main__":
        asyncio.run(update_loop())