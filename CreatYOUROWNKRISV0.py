import sys
import math
import pygame

# Constants
TILE_SIZE = 32
LEVEL = [
    "####################",
    "#..................#",
    "#..######..........#",
    "#..................#",
    "#...........####...#",
    "#..................#",
    "#..................#",
    "####################",
]

WIDTH = len(LEVEL[0]) * TILE_SIZE
HEIGHT = len(LEVEL) * TILE_SIZE

# Initialize Pygame
pygame.init()
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Deltarune Overworld Demo")
CLOCK = pygame.time.Clock()

# Basic graphics
WALL_IMG = pygame.Surface((TILE_SIZE, TILE_SIZE))
WALL_IMG.fill((60, 60, 60))
FLOOR_IMG = pygame.Surface((TILE_SIZE, TILE_SIZE))
FLOOR_IMG.fill((10, 10, 40))
PLAYER_IMG = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
pygame.draw.circle(PLAYER_IMG, (255, 255, 0), (TILE_SIZE // 2, TILE_SIZE // 2), TILE_SIZE // 2)

# Player setup
player = PLAYER_IMG.get_rect()
player.topleft = (TILE_SIZE * 2, TILE_SIZE * 2)
SPEED = 160  # pixels per second

# Helper to check tile collisions
def is_wall(px, py):
    if 0 <= py < len(LEVEL) and 0 <= px < len(LEVEL[0]):
        return LEVEL[py][px] == '#'
    return True

# Main loop
running = True
target_pos = None
while running:
    dt = CLOCK.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            target_pos = event.pos

    keys = pygame.key.get_pressed()
    dx = dy = 0
    if target_pos:
        cx, cy = player.center
        tx, ty = target_pos
        vec_x = tx - cx
        vec_y = ty - cy
        dist = math.hypot(vec_x, vec_y)
        if dist > 1:
            dx = (vec_x / dist) * SPEED * dt
            dy = (vec_y / dist) * SPEED * dt
        else:
            target_pos = None
    else:
        if keys[pygame.K_LEFT]:
            dx = -SPEED * dt
        if keys[pygame.K_RIGHT]:
            dx = SPEED * dt
        if keys[pygame.K_UP]:
            dy = -SPEED * dt
        if keys[pygame.K_DOWN]:
            dy = SPEED * dt

    # Attempt horizontal movement
    new_rect = player.move(dx, 0)
    if not (
        is_wall(new_rect.left // TILE_SIZE, new_rect.top // TILE_SIZE) or
        is_wall(new_rect.right // TILE_SIZE, new_rect.top // TILE_SIZE) or
        is_wall(new_rect.left // TILE_SIZE, new_rect.bottom // TILE_SIZE) or
        is_wall(new_rect.right // TILE_SIZE, new_rect.bottom // TILE_SIZE)
    ):
        player = new_rect

    # Attempt vertical movement
    new_rect = player.move(0, dy)
    if not (
        is_wall(new_rect.left // TILE_SIZE, new_rect.top // TILE_SIZE) or
        is_wall(new_rect.right // TILE_SIZE, new_rect.top // TILE_SIZE) or
        is_wall(new_rect.left // TILE_SIZE, new_rect.bottom // TILE_SIZE) or
        is_wall(new_rect.right // TILE_SIZE, new_rect.bottom // TILE_SIZE)
    ):
        player = new_rect

    # Drawing
    SCREEN.fill((0, 0, 0))
    for y, row in enumerate(LEVEL):
        for x, ch in enumerate(row):
            pos = (x * TILE_SIZE, y * TILE_SIZE)
            if ch == '#':
                SCREEN.blit(WALL_IMG, pos)
            else:
                SCREEN.blit(FLOOR_IMG, pos)
    SCREEN.blit(PLAYER_IMG, player)
    pygame.display.flip()

pygame.quit()
sys.exit()
