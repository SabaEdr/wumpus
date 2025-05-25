import pygame
import random

CELL_SIZE = 50
GRID_SIZE = 10
WIDTH, HEIGHT = CELL_SIZE * GRID_SIZE, CELL_SIZE * GRID_SIZE + 100

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
pygame.display.set_caption("Wumpus Hunt - AI Agent")
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
                    # اگر بخواهیم بعد از مردن Wumpus مخفی کنیم، این را تغییر دهید
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

def check_game_over():
    x, y = player_pos
    cell = board[y][x]
    if cell == 'P':
        return "You fell into a pit! Game Over!"
    if (x,y) in wumpus_alive:
        return "You were eaten by a Wumpus! Game Over!"
    return None

def collect_gold():
    global collected_gold
    x, y = player_pos
    if board[y][x] == 'G':
        collected_gold += 1
        board[y][x] = ' '
        return True
    return False

def draw_text_lines(lines, start_y):
    for i, line in enumerate(lines):
        msg = font.render(line, True, WHITE)
        screen.blit(msg, (10, start_y + i*25))


# ----- هوش مصنوعی (Agent) -----
knowledge = [['unknown' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
knowledge[0][0] = 'safe'

def update_knowledge(pos):
    x, y = pos
    knowledge[y][x] = 'safe'

    # بررسی خانه‌های همسایه برای بوی بد و باد
    for nx, ny in neighbors(pos):
        if knowledge[ny][nx] == 'unknown':
            has_stench = False
            has_breeze = False
            
            # بررسی بوی بد
            for n2x, n2y in neighbors((nx, ny)):
                if (n2x, n2y) in wumpus_alive:
                    has_stench = True
                    break
            
            # بررسی باد
            for n2x, n2y in neighbors((nx, ny)):
                if board[n2y][n2x] == 'P':
                    has_breeze = True
                    break
            
            # به‌روزرسانی دانش بر اساس مشاهدات
            if has_stench and has_breeze:
                knowledge[ny][nx] = 'dangerous'
            elif has_stench:
                knowledge[ny][nx] = 'wumpus?'
            elif has_breeze:
                knowledge[ny][nx] = 'pit?'
            else:
                knowledge[ny][nx] = 'safe'

    # بررسی خانه‌های قبلی برای به‌روزرسانی دانش
    for nx, ny in neighbors(pos):
        if (nx, ny) in visited:
            safe_neighbors = 0
            for n2x, n2y in neighbors((nx, ny)):
                if knowledge[n2y][n2x] == 'safe':
                    safe_neighbors += 1
            
            # اگر همه همسایه‌های یک خانه امن هستند، آن خانه هم امن است
            if safe_neighbors == len(neighbors((nx, ny))):
                knowledge[ny][nx] = 'safe'

def choose_next_move():
    x, y = player_pos
    
    # بررسی وجود بوی بد یا باد در موقعیت فعلی
    has_stench = False
    has_breeze = False
    for nx, ny in neighbors(player_pos):
        if (nx, ny) in wumpus_alive:
            has_stench = True
        if board[ny][nx] == 'P':
            has_breeze = True
    
    # اگر در موقعیت فعلی بوی بد یا باد وجود دارد، به عقب برگرد
    if has_stench or has_breeze:
        # به دنبال خانه امن قبلی بگرد
        for nx, ny in neighbors(player_pos):
            if (nx, ny) in visited and knowledge[ny][nx] == 'safe':
                return (nx, ny), f"Moving back to safe cell { (nx, ny) }"
    
    # اگر در موقعیت امن هستیم، به سمت جلو حرکت کن
    # اولویت با حرکت به سمت راست و پایین است
    preferred_directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]  # راست، پایین، چپ، بالا
    for dx, dy in preferred_directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
            if knowledge[ny][nx] == 'safe' and (nx, ny) not in visited:
                return (nx, ny), f"Moving forward to { (nx, ny) }"
    
    # اگر خانه‌ای در جهت‌های ترجیحی نبود، به هر خانه امنی حرکت کن
    for nx, ny in neighbors(player_pos):
        if knowledge[ny][nx] == 'safe' and (nx, ny) not in visited:
            return (nx, ny), f"Moving to safe unvisited cell { (nx, ny) }"
    
    # اگر خانه امن و بازدید نشده‌ای نبود، به خانه امن بازدید شده برو
    for nx, ny in neighbors(player_pos):
        if knowledge[ny][nx] == 'safe' and (nx, ny) != tuple(player_pos):
            return (nx, ny), f"Moving to known safe cell { (nx, ny) }"
    
    # اگر خانه‌ای احتمال وومپوس دارد و تیر داریم، شلیک کنیم
    for nx, ny in neighbors(player_pos):
        if knowledge[ny][nx] == 'wumpus?' and player_arrows > 0:
            return 'shoot', (nx, ny), f"Shooting arrow to suspected Wumpus at {(nx, ny)}"
    
    # اگر هیچ راهی نیست، به خانه‌ای که احتمال خطر کمتری دارد حرکت کنیم
    unknown_cells = []
    for nx, ny in neighbors(player_pos):
        if knowledge[ny][nx] == 'unknown' and (nx, ny) != tuple(player_pos):
            unknown_cells.append((nx, ny))
    
    if unknown_cells:
        next_pos = random.choice(unknown_cells)
        return next_pos, f"Moving to unknown cell {next_pos}"
    
    # اگر هیچ راهی نیست بمونیم سر جاش
    return player_pos, f"No safe moves found, staying put."

def agent_step():
    global player_pos, player_arrows, collected_gold, visited, wumpus_alive

    update_knowledge(player_pos)

    action = choose_next_move()

    # حالت شلیک تیر
    if action[0] == 'shoot':
        target = action[1]
        reason = action[2]
        tx, ty = target
        msg = ""
        if (tx, ty) in wumpus_alive:
            wumpus_alive.remove((tx, ty))
            board[ty][tx] = ' '
            msg = f"Killed Wumpus at {(tx, ty)}."
        else:
            msg = "No Wumpus at targeted cell."
        player_arrows -= 1
        return reason + " " + msg

    # حالت حرکت
    elif isinstance(action[0], tuple):
        new_pos = action[0]
        reason = action[1]
        player_pos[:] = new_pos
        visited.add(tuple(player_pos))
        if collect_gold():
            return f"Moved to {new_pos} and collected gold."
        return reason

    # حالت بمونیم سرجاش
    else:
        reason = action[1]
        return reason

# ----- پایان هوش مصنوعی -----

def main():
    global player_pos, player_arrows, collected_gold
    running = True
    message_lines = ["Agent started."]
    clock = pygame.time.Clock()

    game_over = False

    while running:
        screen.fill(BLACK)
        draw_grid()
        draw_objects()
        draw_player()
        draw_messages_on_cells()

        # پیام‌ها (استدلال عامل) را پایین صفحه نمایش بده
        draw_text_lines(message_lines[-4:], GRID_SIZE*CELL_SIZE + 10)

        if not game_over:
            msg = agent_step()
            message_lines.append(msg)
            result = check_game_over()
            if result:
                message_lines.append(result)
                game_over = True
        else:
            message_lines.append("Press ESC to exit.")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        pygame.display.flip()
        clock.tick(1)  # یک حرکت در ثانیه برای دیدن بهتر تصمیم‌ها

    pygame.quit()

if __name__ == "__main__":
    main()
