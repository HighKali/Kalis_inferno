import pygame
import random
import math
from queue import PriorityQueue

# Inizializzazione Pygame
pygame.init()

# Costanti
WIDTH, HEIGHT = 800, 600
TILE_SIZE = 32
FPS = 60

# Colori
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
BLUE = (0, 0, 255)
GREY = (50, 50, 50)

# Schermo
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Horror Retro RPG - Berzerk Reimagined")
clock = pygame.time.Clock()

# Classe per il giocatore (Kali)
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 3
        self.rect = pygame.Rect(self.x, self.y, TILE_SIZE, TILE_SIZE)
        self.panther = Panther(self.x + TILE_SIZE, self.y)
        self.inventory = []
        self.health = 100
        self.sanity = 100
        self.attack_cooldown = 0

    def move(self, dx, dy, walls):
        self.rect.x += dx * self.speed
        self.rect.y += dy * self.speed
        for wall in walls:
            if self.rect.colliderect(wall):
                self.rect.x -= dx * self.speed
                self.rect.y -= dy * self.speed
        self.panther.update(self.x, self.y)
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    def attack(self, enemies):
        if self.attack_cooldown == 0:
            for enemy in enemies:
                if math.dist((self.rect.centerx, self.rect.centery), (enemy.rect.centerx, enemy.rect.centery)) < 50:
                    enemy.health -= 25
                    self.attack_cooldown = 20
                    return True
        return False

    def draw(self):
        pygame.draw.rect(screen, WHITE, self.rect)
        self.draw_sword()
        self.panther.draw()
        pygame.draw.rect(screen, RED, (self.rect.x, self.rect.y - 10, self.health // 2, 5))
        pygame.draw.rect(screen, BLUE, (self.rect.x, self.rect.y - 15, self.sanity // 2, 5))

    def draw_sword(self):
        for i in range(5):
            offset = random.randint(-2, 2)
            pygame.draw.line(screen, (255, 100 + i * 20, 0), 
                            (self.rect.right, self.rect.centery), 
                            (self.rect.right + 20 + offset, self.rect.centery + offset), 3)

# Classe per la pantera
class Panther:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

    def update(self, player_x, player_y):
        self.rect.x = player_x + TILE_SIZE
        self.rect.y = player_y

    def draw(self):
        pygame.draw.rect(screen, GREEN, self.rect)

# Classe per i nemici
class Enemy:
    def __init__(self, x, y, type="cerberus"):
        self.x = x
        self.y = y
        self.type = type
        self.rect = pygame.Rect(self.x, self.y, TILE_SIZE, TILE_SIZE)
        self.speed = 2 if type != "baphomet" else 3
        self.health = 50 if type != "baphomet" else 200

    def a_star(self, start, goal, walls):
        frontier = PriorityQueue()
        frontier.put((0, start))
        came_from = {}
        cost_so_far = {start: 0}
        while not frontier.empty():
            current = frontier.get()[1]
            if current == goal:
                break
            for next in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                new_pos = (current[0] + next[0], current[1] + next[1])
                if 0 <= new_pos[0] < WIDTH // TILE_SIZE and 0 <= new_pos[1] < HEIGHT // TILE_SIZE and \
                   not any(pygame.Rect(new_pos[0] * TILE_SIZE, new_pos[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE).colliderect(w) for w in walls):
                    new_cost = cost_so_far[current] + 1
                    if new_pos not in cost_so_far or new_cost < cost_so_far[new_pos]:
                        cost_so_far[new_pos] = new_cost
                        priority = new_cost + math.dist(new_pos, goal)
                        frontier.put((priority, new_pos))
                        came_from[new_pos] = current
        path = []
        current = goal
        while current != start:
            path.append(current)
            current = came_from.get(current, start)
        return path[::-1] if path else []

    def move_towards(self, target, walls):
        start = (self.rect.x // TILE_SIZE, self.rect.y // TILE_SIZE)
        goal = (target.rect.x // TILE_SIZE, target.rect.y // TILE_SIZE)
        path = self.a_star(start, goal, walls)
        if path and len(path) > 1:
            next_step = path[1]
            self.rect.x = next_step[0] * TILE_SIZE
            self.rect.y = next_step[1] * TILE_SIZE

    def draw(self):
        color = RED if self.type in ["cerberus", "medusa"] else YELLOW if self.type in ["griffin", "phoenix"] else PURPLE if self.type == "baphomet" else BLUE
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, RED, (self.rect.x, self.rect.y - 10, self.health // 4, 5))

# Classe per le trappole
class Trap:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.active = True

    def trigger(self, player):
        if self.active and player.rect.colliderect(self.rect):
            player.health -= 15
            player.sanity -= 10
            self.active = False
            print("Trappola attivata!")

    def draw(self):
        if self.active:
            pygame.draw.rect(screen, GREY, self.rect)

# Generazione labirinto
def generate_maze(width, height):
    grid = [[1 for _ in range(width)] for _ in range(height)]
    def carve(x, y, w, h):
        if w < 2 or h < 2:
            return
        horizontal = random.choice([True, False]) if w > h else False
        if horizontal:
            wall_y = y + random.randint(1, h - 2)
            passage_x = x + random.randint(0, w - 1)
            for i in range(w):
                if i != passage_x:
                    grid[wall_y][x + i] = 1
            carve(x, y, w, wall_y - y)
            carve(x, wall_y + 1, w, h - (wall_y - y + 1))
        else:
            wall_x = x + random.randint(1, w - 2)
            passage_y = y + random.randint(0, h - 1)
            for i in range(h):
                if i != passage_y:
                    grid[y + i][wall_x] = 1
            carve(x, y, wall_x - x, h)
            carve(wall_x + 1, y, w - (wall_x - x + 1), h)
    carve(0, 0, width, height)
    return grid

# Livello 1: Bosco con castello abbandonato
def level_1(player):
    walls = [pygame.Rect(0, 0, WIDTH, TILE_SIZE), pygame.Rect(0, HEIGHT - TILE_SIZE, WIDTH, TILE_SIZE),
             pygame.Rect(0, 0, TILE_SIZE, HEIGHT), pygame.Rect(WIDTH - TILE_SIZE, 0, TILE_SIZE, HEIGHT)]
    maze = generate_maze(WIDTH // TILE_SIZE - 2, HEIGHT // TILE_SIZE - 2)
    for y, row in enumerate(maze):
        for x, cell in enumerate(row):
            if cell:
                walls.append(pygame.Rect((x + 1) * TILE_SIZE, (y + 1) * TILE_SIZE, TILE_SIZE, TILE_SIZE))
    items = {"scroll": pygame.Rect(200, 200, TILE_SIZE, TILE_SIZE),
             "backpack": pygame.Rect(300, 300, TILE_SIZE, TILE_SIZE),
             "key": pygame.Rect(400, 400, TILE_SIZE, TILE_SIZE)}
    gate = pygame.Rect(WIDTH - TILE_SIZE * 2, HEIGHT // 2, TILE_SIZE * 2, TILE_SIZE * 2)
    enemies = [Enemy(500, 500, "medusa")]
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                player.attack(enemies)
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]: dx = -1
        if keys[pygame.K_RIGHT]: dx = 1
        if keys[pygame.K_UP]: dy = -1
        if keys[pygame.K_DOWN]: dy = 1
        player.move(dx, dy, walls)
        for enemy in enemies[:]:
            enemy.move_towards(player, walls)
            if player.rect.colliderect(enemy.rect):
                player.health -= 10
            if enemy.health <= 0:
                enemies.remove(enemy)
        if player.health <= 0:
            return False
        for item, rect in items.items():
            if player.rect.colliderect(rect):
                player.inventory.append(item)
                del items[item]
                break
        if "key" in player.inventory and player.rect.colliderect(gate):
            return True
        screen.fill(BLACK)
        pygame.draw.circle(screen, YELLOW, (WIDTH - 100, 100), 50)
        pygame.draw.circle(screen, BLACK, (WIDTH - 110, 90), 10)
        pygame.draw.circle(screen, BLACK, (WIDTH - 90, 90), 10)
        pygame.draw.arc(screen, BLACK, (WIDTH - 120, 100, 40, 20), 0, math.pi, 3)
        for wall in walls:
            pygame.draw.rect(screen, WHITE, wall)
        for rect in items.values():
            pygame.draw.rect(screen, GREEN, rect)
        pygame.draw.rect(screen, RED, gate)
        player.draw()
        for enemy in enemies:
            enemy.draw()
        pygame.display.flip()
        clock.tick(FPS)
    return False

# Livello 2: Castello inquietante
def level_2(player):
    walls = [pygame.Rect(0, 0, WIDTH, TILE_SIZE), pygame.Rect(0, HEIGHT - TILE_SIZE, WIDTH, TILE_SIZE),
             pygame.Rect(0, 0, TILE_SIZE, HEIGHT), pygame.Rect(WIDTH - TILE_SIZE, 0, TILE_SIZE, HEIGHT)]
    maze = generate_maze(WIDTH // TILE_SIZE - 2, HEIGHT // TILE_SIZE - 2)
    for y, row in enumerate(maze):
        for x, cell in enumerate(row):
            if cell:
                walls.append(pygame.Rect((x + 1) * TILE_SIZE, (y + 1) * TILE_SIZE, TILE_SIZE, TILE_SIZE))
    enemies = [Enemy(random.randint(100, 700), random.randint(100, 500), "griffin") for _ in range(3)]
    enigma_rect = pygame.Rect(300, 300, TILE_SIZE, TILE_SIZE)
    enigma_solved = False
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                player.attack(enemies)
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]: dx = -1
        if keys[pygame.K_RIGHT]: dx = 1
        if keys[pygame.K_UP]: dy = -1
        if keys[pygame.K_DOWN]: dy = 1
        player.move(dx, dy, walls)
        for enemy in enemies[:]:
            enemy.move_towards(player, walls)
            if player.rect.colliderect(enemy.rect):
                player.health -= 15
            if enemy.health <= 0:
                enemies.remove(enemy)
        if player.health <= 0:
            return False
        if not enigma_solved and player.rect.colliderect(enigma_rect):
            print("Enigma: Ordina gli elementi: Fuoco, Acqua, Terra, Aria")
            answer = input("Risposta: ")
            if answer.lower() == "fuoco, acqua, terra, aria":
                enigma_solved = True
                return True
        screen.fill(BLACK)
        for wall in walls:
            pygame.draw.rect(screen, WHITE, wall)
        pygame.draw.rect(screen, YELLOW, enigma_rect)
        player.draw()
        for enemy in enemies:
            enemy.draw()
        pygame.display.flip()
        clock.tick(FPS)
    return False

# Livello 3: Catacombe delle Ombre (Espanso)
def level_3(player):
    walls = [pygame.Rect(0, 0, WIDTH, TILE_SIZE), pygame.Rect(0, HEIGHT - TILE_SIZE, WIDTH, TILE_SIZE),
             pygame.Rect(0, 0, TILE_SIZE, HEIGHT), pygame.Rect(WIDTH - TILE_SIZE, 0, TILE_SIZE, HEIGHT)]
    maze = generate_maze(WIDTH // TILE_SIZE - 2, HEIGHT // TILE_SIZE - 2)
    for y, row in enumerate(maze):
        for x, cell in enumerate(row):
            if cell:
                walls.append(pygame.Rect((x + 1) * TILE_SIZE, (y + 1) * TILE_SIZE, TILE_SIZE, TILE_SIZE))
    enemies = [Enemy(random.randint(100, 700), random.randint(100, 500), "cerberus") for _ in range(2)] + \
              [Enemy(random.randint(100, 700), random.randint(100, 500), "wraith") for _ in range(3)]
    skull_key = pygame.Rect(600, 400, TILE_SIZE, TILE_SIZE)
    bone_shard = pygame.Rect(200, 200, TILE_SIZE, TILE_SIZE)
    shadow_gem = pygame.Rect(300, 300, TILE_SIZE, TILE_SIZE)
    exit_gate = pygame.Rect(WIDTH - TILE_SIZE * 2, HEIGHT - TILE_SIZE * 2, TILE_SIZE, TILE_SIZE)
    traps = [Trap(random.randint(100, 700), random.randint(100, 500)) for _ in range(5)]
    enigma_altar = pygame.Rect(500, 200, TILE_SIZE, TILE_SIZE)
    enigma_solved = False
    shadow_alpha = 0
    shadow_direction = 1
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                player.attack(enemies)
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]: dx = -1
        if keys[pygame.K_RIGHT]: dx = 1
        if keys[pygame.K_UP]: dy = -1
        if keys[pygame.K_DOWN]: dy = 1
        player.move(dx, dy, walls)
        for enemy in enemies[:]:
            enemy.move_towards(player, walls)
            if player.rect.colliderect(enemy.rect):
                player.health -= 20 if enemy.type == "cerberus" else 15
                player.sanity -= 5 if enemy.type == "wraith" else 0
            if enemy.health <= 0:
                enemies.remove(enemy)
        if player.health <= 0 or player.sanity <= 0:
            return False
        for trap in traps:
            trap.trigger(player)
        if player.rect.colliderect(skull_key):
            player.inventory.append("skull_key")
            skull_key = pygame.Rect(-100, -100, 0, 0)
        if player.rect.colliderect(bone_shard):
            player.inventory.append("bone_shard")
            bone_shard = pygame.Rect(-100, -100, 0, 0)
        if player.rect.colliderect(shadow_gem):
            player.inventory.append("shadow_gem")
            shadow_gem = pygame.Rect(-100, -100, 0, 0)
        if not enigma_solved and player.rect.colliderect(enigma_altar) and \
           "bone_shard" in player.inventory and "shadow_gem" in player.inventory:
            print("Enigma: Una volta ero vivo, ora sono polvere. La mia ombra è eterna, ma la luce mi spegne. Cosa sono?")
            answer = input("Risposta: ")
            if answer.lower() in ["scheletro", "skeleton"]:
                enigma_solved = True
                player.sanity = min(player.sanity + 20, 100)
            else:
                player.sanity -= 10
        if "skull_key" in player.inventory and enigma_solved and player.rect.colliderect(exit_gate):
            return True
        screen.fill(BLACK)
        shadow_alpha += shadow_direction * 2
        if shadow_alpha >= 100 or shadow_alpha <= 0:
            shadow_direction *= -1
        shadow_surface = pygame.Surface((WIDTH, HEIGHT))
        shadow_surface.set_alpha(shadow_alpha)
        shadow_surface.fill(PURPLE)
        screen.blit(shadow_surface, (0, 0))
        for wall in walls:
            pygame.draw.rect(screen, PURPLE, wall)
        for trap in traps:
            trap.draw()
        pygame.draw.rect(screen, GREEN, skull_key)
        pygame.draw.rect(screen, WHITE, bone_shard)
        pygame.draw.rect(screen, BLUE, shadow_gem)
        pygame.draw.rect(screen, RED, exit_gate)
        pygame.draw.rect(screen, YELLOW, enigma_altar)
        player.draw()
        for enemy in enemies:
            enemy.draw()
        font = pygame.font.Font(None, 36)
        sanity_text = font.render(f"Sanità: {player.sanity}", True, WHITE)
        screen.blit(sanity_text, (10, 10))
        pygame.display.flip()
        clock.tick(FPS)
    return False

# Livello 4: Tempio della Fenice
def level_4(player):
    walls = [pygame.Rect(0, 0, WIDTH, TILE_SIZE), pygame.Rect(0, HEIGHT - TILE_SIZE, WIDTH, TILE_SIZE),
             pygame.Rect(0, 0, TILE_SIZE, HEIGHT), pygame.Rect(WIDTH - TILE_SIZE, 0, TILE_SIZE, HEIGHT)]
    maze = generate_maze(WIDTH // TILE_SIZE - 2, HEIGHT // TILE_SIZE - 2)
    for y, row in enumerate(maze):
        for x, cell in enumerate(row):
            if cell:
                walls.append(pygame.Rect((x + 1) * TILE_SIZE, (y + 1) * TILE_SIZE, TILE_SIZE, TILE_SIZE))
    enemies = [Enemy(random.randint(100, 700), random.randint(100, 500), "phoenix") for _ in range(3)]
    flame_altar = pygame.Rect(400, 300, TILE_SIZE, TILE_SIZE)
    enigma_solved = False
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                player.attack(enemies)
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]: dx = -1
        if keys[pygame.K_RIGHT]: dx = 1
        if keys[pygame.K_UP]: dy = -1
        if keys[pygame.K_DOWN]: dy = 1
        player.move(dx, dy, walls)
        for enemy in enemies[:]:
            enemy.move_towards(player, walls)
            if player.rect.colliderect(enemy.rect):
                player.health -= 25
            if enemy.health <= 0:
                enemies.remove(enemy)
        if player.health <= 0:
            return False
        if not enigma_solved and player.rect.colliderect(flame_altar):
            print("Enigma: Qual è l'elemento che rinasce dalle sue ceneri?")
            answer = input("Risposta: ")
            if answer.lower() in ["fuoco", "fenice"]:
                enigma_solved = True
                return True
        screen.fill(BLACK)
        for wall in walls:
            pygame.draw.rect(screen, YELLOW, wall)
        pygame.draw.rect(screen, RED, flame_altar)
        player.draw()
        for enemy in enemies:
            enemy.draw()
        pygame.display.flip()
        clock.tick(FPS)
    return False

# Livello 5-14: Generico con difficoltà crescente
def generic_level(player, level_num):
    walls = [pygame.Rect(0, 0, WIDTH, TILE_SIZE), pygame.Rect(0, HEIGHT - TILE_SIZE, WIDTH, TILE_SIZE),
             pygame.Rect(0, 0, TILE_SIZE, HEIGHT), pygame.Rect(WIDTH - TILE_SIZE, 0, TILE_SIZE, HEIGHT)]
    maze = generate_maze(WIDTH // TILE_SIZE - 2, HEIGHT // TILE_SIZE - 2)
    for y, row in enumerate(maze):
        for x, cell in enumerate(row):
            if cell:
                walls.append(pygame.Rect((x + 1) * TILE_SIZE, (y + 1) * TILE_SIZE, TILE_SIZE, TILE_SIZE))
    enemy_types = ["siren", "giant", "minotaur", "dragon", "wraith", "titan", "chimera"]
    enemies = [Enemy(random.randint(100, 700), random.randint(100, 500), random.choice(enemy_types)) 
               for _ in range(max(2, level_num // 2))]
    exit_gate = pygame.Rect(WIDTH - TILE_SIZE * 2, HEIGHT - TILE_SIZE * 2, TILE_SIZE, TILE_SIZE)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                player.attack(enemies)
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]: dx = -1
        if keys[pygame.K_RIGHT]: dx = 1
        if keys[pygame.K_UP]: dy = -1
        if keys[pygame.K_DOWN]: dy = 1
        player.move(dx, dy, walls)
        for enemy in enemies[:]:
            enemy.move_towards(player, walls)
            if player.rect.colliderect(enemy.rect):
                player.health -= 20 + level_num * 2
            if enemy.health <= 0:
                enemies.remove(enemy)
        if player.health <= 0:
            return False
        if player.rect.colliderect(exit_gate):
            return True
        screen.fill((random.randint(0, 50), 0, random.randint(0, 50)))
        for wall in walls:
            pygame.draw.rect(screen, WHITE, wall)
        pygame.draw.rect(screen, RED, exit_gate)
        player.draw()
        for enemy in enemies:
            enemy.draw()
        pygame.display.flip()
        clock.tick(FPS)
    return False

# Livello 15: Baphomet
def level_15(player):
    baphomet = Enemy(400, 300, "baphomet")
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                player.attack([baphomet])
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]: dx = -1
        if keys[pygame.K_RIGHT]: dx = 1
        if keys[pygame.K_UP]: dy = -1
        if keys[pygame.K_DOWN]: dy = 1
        player.move(dx, dy, [])
        baphomet.move_towards(player, [])
        if player.rect.colliderect(baphomet.rect):
            player.health -= 30
        if baphomet.health <= 0:
            return True
        if player.health <= 0:
            return False
        screen.fill(BLACK)
        pygame.draw.circle(screen, RED, (WIDTH // 2, HEIGHT // 2), 100, 5)
        player.draw()
        baphomet.draw()
        pygame.display.flip()
        clock.tick(FPS)
    return False

# Finale psichedelico
def psychedelic_ending():
    print("Kali incontra Lilith e il suo ghepardo. Insieme, intraprendono un viaggio astrale psichedelico...")
    for _ in range(100):
        screen.fill((random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        for _ in range(5):
            pygame.draw.circle(screen, (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), 
                              (random.randint(0, WIDTH), random.randint(0, HEIGHT)), random.randint(10, 50))
        pygame.display.flip()
        pygame.time.delay(50)
    print("Fine del gioco.")

# Gioco principale
def main():
    player = Player(50, 50)
    levels = [level_1, level_2, level_3, level_4]
    for i in range(5, 15):
        levels.append(lambda p, n=i: generic_level(p, n))
    levels.append(level_15)
    for i, level in enumerate(levels, 1):
        player.health = 100
        player.sanity = 100
        if level(player):
            print(f"Livello {i} completato!")
        else:
            print(f"Game Over al livello {i}!")
            break
    else:
        psychedelic_ending()
    pygame.quit()

if __name__ == "__main__":
    main()
