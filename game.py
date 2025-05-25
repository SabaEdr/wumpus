import pygame
import random

CELL_SIZE = 50
GRID_SIZE = 10
WIDTH, HEIGHT = CELL_SIZE * GRID_SIZE, CELL_SIZE * GRID_SIZE + 80

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
LIGHT_GRAY = (180, 180, 180)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 200, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (160, 32, 240)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wumpus Hunt with Shooting")
font = pygame.font.SysFont(None, 24)
small_font = pygame.font.SysFont(None, 18)

board = [[' ' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
NUM_WUMPUS = 4
NUM_PITS = 6
NUM_GOLD = 5

player_pos = [0, 0]
player_arrows = 3
collected_gold = 0
visited = set()
visited.add((0, 0))  # خانه شروع بازدید شده است
wumpus_alive = set()  # مختصات Wumpus‌های زنده

def neighbors(pos):
    x, y = pos
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1)]
    result = []
    for dx, dy in dirs:
        nx, ny = x + dx, y + dy
        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
            result.append((nx, ny))
    return result

def place_objects():
    forbidden = [(0, 0)] + neighbors((0, 0))
    count = 0
    while count < NUM_WUMPUS:
        x, y = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
        if (x,y) not in forbidden and board[y][x] == ' ':
            board[y][x] = 'W'
            wumpus_alive.add((x,y))
            count += 1
    count = 0
    while count < NUM_PITS:
        x, y = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
        if (x,y) not in forbidden and board[y][x] == ' ':
            board[y][x] = 'P'
            count += 1
    count = 0
    while count < NUM_GOLD:
        x, y = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
        if (x,y) not in forbidden and board[y][x] == ' ':
            board[y][x] = 'G'
            count += 1

place_objects()

def draw_grid():
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            rect = pygame.Rect(x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if (x,y) in visited:
                pygame.draw.rect(screen, LIGHT_GRAY, rect)  # خانه بازدید شده
            else:
                pygame.draw.rect(screen, GRAY, rect)  # خانه بسته
            pygame.draw.rect(screen, BLACK, rect, 1)  # خطوط شبکه

def draw_objects():
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            cell = board[y][x]
            rect = pygame.Rect(x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if (x,y) in visited:
                if cell == 'G':
                    pygame.draw.circle(screen, YELLOW, rect.center, CELL_SIZE//4)
                elif cell == 'W':
                    pygame.draw.circle(screen, RED, rect.center, CELL_SIZE//4)
                elif cell == 'P':
                    pygame.draw.rect(screen, BLUE, rect.inflate(-20, -20))

def draw_player():
    x, y = player_pos
    rect = pygame.Rect(x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE)
    pygame.draw.rect(screen, GREEN, rect.inflate(-10, -10))

def draw_messages_on_cells():
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            if (x,y) in visited:
                rect = pygame.Rect(x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                msgs = []
                # بوی بد (Wumpus alive در 8 جهت)
                for nx, ny in neighbors((x,y)):
                    if (nx, ny) in wumpus_alive:
                        msgs.append("Stench")
                        break
                # باد (Pit در 8 جهت)
                for nx, ny in neighbors((x,y)):
                    if board[ny][nx] == 'P':
                        msgs.append("Breeze")
                        break
                y_offset = 5
                for msg in msgs:
                    text_surf = small_font.render(msg, True, ORANGE if msg=="Stench" else BLUE)
                    screen.blit(text_surf, (rect.x + 2, rect.y + y_offset))
                    y_offset += 16

def smells_and_breeze():
    messages = []
    px, py = player_pos
    for nx, ny in neighbors((px, py)):
        if (nx, ny) in wumpus_alive:
            messages.append("You smell a foul stench nearby!")
            break
    for nx, ny in neighbors((px, py)):
        if board[ny][nx] == 'P':
            messages.append("You feel a breeze nearby!")
            break
    return messages

def check_game_over():
    x, y = player_pos
    cell = board[y][x]
    if cell == 'P':
        return "You fell into a pit! Game Over!"
    if (x,y) in wumpus_alive:
        return "You were eaten by a Wumpus! Game Over!"
    return None

def collect_gold():
    global collected_gold, show_gold_acquired_message_timer
    x, y = player_pos
    if board[y][x] == 'G':
        collected_gold += 1
        board[y][x] = ' '
        show_gold_acquired_message_timer = 60 # Display message for 60 frames
        return True
    return False

def draw_text_lines(lines, start_y):
    for i, line in enumerate(lines):
        msg = font.render(line, True, WHITE)
        screen.blit(msg, (10, start_y + i*25))

# جهت تیراندازی ذخیره می‌شود
shoot_direction = None
show_gold_acquired_message_timer = 0 # Timer for "GOLD ACQUIRED!" message

def get_target_from_direction(pos, direction):
    x, y = pos
    dirs = {
        'UP': (x, y-1),
        'DOWN': (x, y+1),
        'LEFT': (x-1, y),
        'RIGHT': (x+1, y),
        'UPLEFT': (x-1, y-1),
        'UPRIGHT': (x+1, y-1),
        'DOWNLEFT': (x-1, y+1),
        'DOWNRIGHT': (x+1, y+1),
    }
    return dirs.get(direction, None)

game_over = False

def main():
    global player_pos, player_arrows, shoot_direction, game_over, show_gold_acquired_message_timer
    running = True
    message_lines = []
    clock = pygame.time.Clock()

    while running:
        screen.fill(BLACK)
        draw_grid()
        draw_objects()
        draw_player()
        draw_messages_on_cells()

        visited.add(tuple(player_pos))

        # پیام‌های بوی بد و باد
        msgs = smells_and_breeze()
        message_lines = msgs if msgs else ["All seems quiet..."]

        game_over_msg = check_game_over()
        if game_over_msg:
            message_lines.append(game_over_msg)
            # اگر بازی باخت، بازی رو متوقف کن
            if "Game Over" in game_over_msg:
                game_over = True

        if collect_gold():
            message_lines.append(f"Gold collected: {collected_gold}/{NUM_GOLD}")

        # پیام جهت تیراندازی فعلی
        if shoot_direction:
            message_lines.append(f"Shoot direction: {shoot_direction}")
        else:
            message_lines.append("No shoot direction selected (press 1-9)")

        draw_text_lines(message_lines, HEIGHT - 70)
        draw_text_lines([f"Arrows left: {player_arrows}"], HEIGHT - 40)

        # Display "GOLD ACQUIRED!" message
        if show_gold_acquired_message_timer > 0:
            gold_msg_font = pygame.font.SysFont(None, 36) # Slightly larger
            text_surf = gold_msg_font.render("GOLD ACQUIRED!", True, YELLOW)
            text_rect = text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50)) # Positioned above center
            screen.blit(text_surf, text_rect)
            show_gold_acquired_message_timer -= 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if game_over:
                # وقتی بازی تمام شد، فقط ESC رو قبول کن
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                continue  # بقیه ورودی‌ها نادیده گرفته میشن

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                new_pos = None
                if event.key == pygame.K_UP:
                    new_pos = [player_pos[0], player_pos[1] - 1]
                elif event.key == pygame.K_DOWN:
                    new_pos = [player_pos[0], player_pos[1] + 1]
                elif event.key == pygame.K_LEFT:
                    new_pos = [player_pos[0] - 1, player_pos[1]]
                elif event.key == pygame.K_RIGHT:
                    new_pos = [player_pos[0] + 1, player_pos[1]]

                if new_pos and 0 <= new_pos[0] < GRID_SIZE and 0 <= new_pos[1] < GRID_SIZE:
                    player_pos = new_pos
                    visited.add(tuple(player_pos))

                # تغییر جهت تیراندازی با کلیدهای 1-9
                if event.key == pygame.K_KP1:
                    shoot_direction = 'DOWNLEFT'
                elif event.key == pygame.K_KP2:
                    shoot_direction = 'DOWN'
                elif event.key == pygame.K_KP3:
                    shoot_direction = 'DOWNRIGHT'
                elif event.key == pygame.K_KP4:
                    shoot_direction = 'LEFT'
                elif event.key == pygame.K_KP5:
                    shoot_direction = None
                elif event.key == pygame.K_KP6:
                    shoot_direction = 'RIGHT'
                elif event.key == pygame.K_KP7:
                    shoot_direction = 'UPLEFT'
                elif event.key == pygame.K_KP8:
                    shoot_direction = 'UP'
                elif event.key == pygame.K_KP9:
                    shoot_direction = 'UPRIGHT'

                # شلیک تیر با Space
                if event.key == pygame.K_SPACE:
                    if player_arrows > 0 and shoot_direction:
                        player_arrows -= 1
                        target = get_target_from_direction(player_pos, shoot_direction)
                        if target:
                            tx, ty = target
                            if 0 <= tx < GRID_SIZE and 0 <= ty < GRID_SIZE:
                                if (tx, ty) in wumpus_alive:
                                    wumpus_alive.remove((tx, ty))
                                    message_lines.append("You killed a Wumpus!")
                                else:
                                    message_lines.append("You missed!")
                            else:
                                message_lines.append("You shot outside the grid!")
                        else:
                            message_lines.append("No valid shoot direction!")
                    else:
                        message_lines.append("No arrows left or no direction selected!")

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()
