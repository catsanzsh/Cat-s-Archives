import sys
import pygame

# Constants
TILE_SIZE = 32

# Rooms mimic a handful of locations from Chapter 1.  They are
# intentionally tiny and only hint at the real maps.
ROOMS = {
    "classroom": [
        "####################",
        "#.......D..........#",
        "#..................#",
        "#....N.............#",
        "#..................#",
        "#..................#",
        "#..................#",
        "####################",
    ],
    "dark_room": [
        "####################",
        "#..................#",
        "#....######........#",
        "#..............D...#",
        "#.....N............#",
        "#..................#",
        "#..................#",
        "####################",
    ],
}
current_room = "classroom"

def get_level():
    return ROOMS[current_room]

WIDTH = len(get_level()[0]) * TILE_SIZE
HEIGHT = len(get_level()) * TILE_SIZE

# Initialize Pygame
pygame.init()
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Deltarune Overworld Demo")
CLOCK = pygame.time.Clock()

# Message UI
FONT = pygame.font.SysFont("Arial", 20)
message = None
message_timer = 0.0

# Player setup
player = pygame.Rect(
    TILE_SIZE * 2, TILE_SIZE * 2, TILE_SIZE // 2, TILE_SIZE // 2
)
PLAYER_COLOR = (255, 255, 0)
SPEED = 160  # pixels per second

# Helper to check tile collisions
def is_wall(px, py):
    level = get_level()
    if 0 <= py < len(level) and 0 <= px < len(level[0]):
        return level[py][px] in ('#', 'N')
    return True

# Main loop
running = True
while running:
    dt = CLOCK.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    dx = dy = 0
    if keys[pygame.K_LEFT]:
        dx = -SPEED * dt
    if keys[pygame.K_RIGHT]:
        dx = SPEED * dt
    if keys[pygame.K_UP]:
        dy = -SPEED * dt
    if keys[pygame.K_DOWN]:
        dy = SPEED * dt

    if keys[pygame.K_z]:
        cx = player.centerx // TILE_SIZE
        cy = player.centery // TILE_SIZE
        level = get_level()
        if 0 <= cy < len(level) and 0 <= cx < len(level[0]):
            if level[cy][cx] == 'N':
                message = "Hi there!"
                message_timer = 2.0

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

    # Door transition: if standing on 'D', move to the other room
    cx = player.centerx // TILE_SIZE
    cy = player.centery // TILE_SIZE
    level = get_level()
    if 0 <= cy < len(level) and 0 <= cx < len(level[0]):
        if level[cy][cx] == 'D' and current_room == "classroom":
            current_room = "dark_room"
            WIDTH = len(get_level()[0]) * TILE_SIZE
            HEIGHT = len(get_level()) * TILE_SIZE
            SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
            player.x, player.y = TILE_SIZE * 2, TILE_SIZE * 2
        elif level[cy][cx] == 'D' and current_room == "dark_room":
            current_room = "classroom"
            WIDTH = len(get_level()[0]) * TILE_SIZE
            HEIGHT = len(get_level()) * TILE_SIZE
            SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
            player.x, player.y = TILE_SIZE * 7, TILE_SIZE * 2

    # Update message timer
    if message_timer > 0:
        message_timer -= dt
        if message_timer <= 0:
            message_timer = 0
            message = None

    # Drawing
    SCREEN.fill((0, 0, 0))
    for y, row in enumerate(get_level()):
        for x, ch in enumerate(row):
            if ch == '#':
                pygame.draw.rect(
                    SCREEN,
                    (60, 60, 60),
                    (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE),
                )
            elif ch == 'D':
                pygame.draw.rect(
                    SCREEN,
                    (0, 0, 255),
                    (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE),
                )
    pygame.draw.rect(SCREEN, PLAYER_COLOR, player)
    if message:
        text_surf = FONT.render(message, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(WIDTH // 2, HEIGHT - 20))
        SCREEN.blit(text_surf, text_rect)
    pygame.display.flip()

pygame.quit()
sys.exit()
