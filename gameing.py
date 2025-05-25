import pygame
import random

# --- Constants and Initialization ---
CELL_SIZE = 50
GRID_SIZE = 10
WIDTH, HEIGHT = CELL_SIZE * GRID_SIZE, CELL_SIZE * GRID_SIZE + 100

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
LIGHT_GRAY = (180, 180, 180)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 200, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wumpus Hunt")
font = pygame.font.SysFont(None, 28)
small_font = pygame.font.SysFont(None, 20)

# --- Game State Variables ---
board = [[' ' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
NUM_WUMPUS = 5
NUM_PITS = 5
NUM_GOLD = 3

player_pos = [0, 0]
player_arrows = NUM_WUMPUS + 1
collected_gold = 0
visited = set()
wumpus_alive = set()

knowledge = [['unknown' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
recently_cleared_wumpus_cell = None
game_over_flag = False
last_player_pos = None
show_gold_acquired_message_timer = 0
display_messages_history = ["Welcome to 8-Way Wumpus World!"]


# --- Helper Functions ---
def get_neighbors(pos, use_eight_directions=True):
    x, y = pos
    if use_eight_directions:
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1),
                (-1, -1), (-1, 1), (1, -1), (1, 1)]
    else:
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    result = []
    for dx, dy in dirs:
        nx, ny = x + dx, y + dy
        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
            result.append((nx, ny))
    return result


def place_objects():
    global board, wumpus_alive
    forbidden = [(0, 0)] + get_neighbors((0, 0), use_eight_directions=True)

    count = 0
    wumpus_alive.clear()
    while count < NUM_WUMPUS:
        x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
        if (x, y) not in forbidden and board[y][x] == ' ':
            board[y][x] = 'W'
            wumpus_alive.add((x, y))
            count += 1

    count = 0
    while count < NUM_PITS:
        x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
        if (x, y) not in forbidden and board[y][x] == ' ':
            board[y][x] = 'P'
            count += 1

    count = 0
    while count < NUM_GOLD:
        x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
        if (x, y) not in forbidden and board[y][x] == ' ':
            board[y][x] = 'G'
            count += 1


def draw_grid():
    for x_coord in range(GRID_SIZE):
        for y_coord in range(GRID_SIZE):
            rect = pygame.Rect(x_coord * CELL_SIZE, y_coord * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if (x_coord, y_coord) in visited:
                pygame.draw.rect(screen, LIGHT_GRAY, rect)
            else:
                pygame.draw.rect(screen, GRAY, rect)
            pygame.draw.rect(screen, BLACK, rect, 1)


def draw_objects():
    for y_obj in range(GRID_SIZE):
        for x_obj in range(GRID_SIZE):
            cell_content = board[y_obj][x_obj]
            rect = pygame.Rect(x_obj * CELL_SIZE, y_obj * CELL_SIZE, CELL_SIZE, CELL_SIZE)

            if (x_obj, y_obj) in visited:
                if cell_content == 'G':
                    pygame.draw.circle(screen, YELLOW, rect.center, CELL_SIZE // 3)
                elif cell_content == 'W' and (x_obj, y_obj) in wumpus_alive:
                    pygame.draw.circle(screen, RED, rect.center, CELL_SIZE // 3)
                elif cell_content == 'W' and (x_obj, y_obj) not in wumpus_alive:
                    pygame.draw.circle(screen, (100, 0, 0), rect.center, CELL_SIZE // 3)  # Killed Wumpus
                elif cell_content == 'P':
                    pygame.draw.rect(screen, BLACK, rect.inflate(-CELL_SIZE // 2.5, -CELL_SIZE // 2.5))


def draw_player():
    px, py = player_pos
    rect = pygame.Rect(px * CELL_SIZE, py * CELL_SIZE, CELL_SIZE, CELL_SIZE)
    pygame.draw.rect(screen, GREEN, rect.inflate(-CELL_SIZE // 5, -CELL_SIZE // 5))


def draw_messages_on_cells():
    for x_cell_msg in range(GRID_SIZE):
        for y_cell_msg in range(GRID_SIZE):
            if (x_cell_msg, y_cell_msg) in visited:
                rect = pygame.Rect(x_cell_msg * CELL_SIZE, y_cell_msg * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                cell_messages = []

                has_stench = any((nx, ny) in wumpus_alive for nx, ny in
                                 get_neighbors((x_cell_msg, y_cell_msg), use_eight_directions=True))
                if has_stench:
                    cell_messages.append(("Stench", ORANGE))

                has_breeze = any(board[ny][nx] == 'P' for nx, ny in
                                 get_neighbors((x_cell_msg, y_cell_msg), use_eight_directions=True))
                if has_breeze:
                    cell_messages.append(("Breeze", BLUE))

                y_offset = 3
                for msg_text, color in cell_messages:
                    text_surf = small_font.render(msg_text, True, color)
                    screen.blit(text_surf, (rect.x + 3, rect.y + y_offset))
                    y_offset += 15


def get_player_perceptions():
    percepts = []
    px, py = player_pos

    is_stench = any((nx, ny) in wumpus_alive for nx, ny in get_neighbors((px, py), use_eight_directions=True))
    if is_stench:
        percepts.append("You smell a foul stench.")

    is_breeze = any(board[ny][nx] == 'P' for nx, ny in get_neighbors((px, py), use_eight_directions=True))
    if is_breeze:
        percepts.append("You feel a breeze.")

    if board[py][px] == 'G':
        percepts.append("You see a glitter!")

    return percepts


def check_game_over():
    global game_over_flag, collected_gold, NUM_GOLD
    px, py = player_pos

    if board[py][px] == 'P':
        game_over_flag = True
        return "You fell into a pit! Game Over!"
    if (px, py) in wumpus_alive:
        game_over_flag = True
        return "Eaten by a Wumpus! Game Over!"
    if collected_gold >= NUM_GOLD:
        game_over_flag = True
        return "Victory! All gold collected!"
    return None


def collect_gold_action():
    global collected_gold, show_gold_acquired_message_timer, board
    px, py = player_pos
    if board[py][px] == 'G':
        collected_gold += 1
        board[py][px] = ' '
        show_gold_acquired_message_timer = 60
        return True
    return False


def draw_game_messages(messages_to_draw, start_y, text_color=WHITE):
    for i, line in enumerate(messages_to_draw):
        msg_surface = font.render(line, True, text_color)
        screen.blit(msg_surface, (10, start_y + i * 25))


# --- AI Agent Logic (8-Way Aware with Logging) ---
def update_knowledge(pos_tuple):
    global knowledge, visited
    x, y = pos_tuple

    knowledge[y][x] = 'safe'
    visited.add(pos_tuple)

    has_stench = any((nx, ny) in wumpus_alive for nx, ny in get_neighbors(pos_tuple, use_eight_directions=True))
    has_breeze = any(board[ny][nx] == 'P' for nx, ny in get_neighbors(pos_tuple, use_eight_directions=True))

    for nx, ny in get_neighbors(pos_tuple, use_eight_directions=True):
        current_neighbor_knowledge = knowledge[ny][nx]

        if not has_stench and not has_breeze:
            knowledge[ny][nx] = 'safe'
        elif not has_stench and has_breeze:
            if current_neighbor_knowledge in ['unknown', 'wumpus?', 'dangerous']:
                knowledge[ny][nx] = 'pit?'
        elif has_stench and not has_breeze:
            if current_neighbor_knowledge in ['unknown', 'pit?', 'dangerous']:
                knowledge[ny][nx] = 'wumpus?'
        elif has_stench and has_breeze:
            if current_neighbor_knowledge in ['unknown', 'wumpus?', 'pit?']:
                knowledge[ny][nx] = 'dangerous'


def choose_next_move():
    global knowledge, player_pos, visited, player_arrows, last_player_pos, recently_cleared_wumpus_cell, collected_gold, NUM_GOLD, board  # Added board for gold check
    current_x, current_y = player_pos

    print(f"\n--- AI Decision at {player_pos} (Arrows: {player_arrows}, Gold: {collected_gold}) ---")
    if last_player_pos: print(f"  Last player pos: {last_player_pos}")
    if recently_cleared_wumpus_cell: print(f"  Recently cleared Wumpus cell flag: {recently_cleared_wumpus_cell}")

    # Priority 0: Move into an adjacent cell where a Wumpus was just killed and is now safe
    print("AI Log: Checking Priority 0 (Move to recently cleared Wumpus cell)")
    if recently_cleared_wumpus_cell:
        rcx, rcy = recently_cleared_wumpus_cell
        is_adj = any((nx, ny) == (rcx, rcy) for nx, ny in get_neighbors(player_pos, use_eight_directions=True))

        if is_adj and knowledge[rcy][rcx] == 'safe':
            action_description = f"Advancing to cleared Wumpus cell ({rcx},{rcy})."
            target_cell_to_move = recently_cleared_wumpus_cell
            recently_cleared_wumpus_cell = None  # Consume the flag
            print(f"  AI DECISION (P0): {action_description} Target: {target_cell_to_move}")
            return (target_cell_to_move, action_description)
        else:
            print(
                f"  AI Log (P0): Recently cleared Wumpus cell {recently_cleared_wumpus_cell} not actionable (adj: {is_adj}, knowledge: {knowledge[rcy][rcx] if recently_cleared_wumpus_cell else 'N/A'}). Clearing flag.")
            recently_cleared_wumpus_cell = None  # Clear if not actionable

    # Priority 1: Grab gold (conceptual, handled by agent_step, but AI can "decide" this)
    print("AI Log: Checking Priority 1 (Grab gold)")
    if board[current_y][current_x] == 'G':
        action_description = "Grabbing gold!"
        print(f"  AI DECISION (P1): {action_description}")
        return ('grab_gold', action_description)

    # Priority 2: Explore safe, unvisited cells (all 8 directions)
    print("AI Log: Checking Priority 2 (Explore safe unvisited)")
    safe_unvisited = []
    for nx, ny in get_neighbors(player_pos, use_eight_directions=True):
        if knowledge[ny][nx] == 'safe' and (nx, ny) not in visited:
            safe_unvisited.append(((nx, ny), f"Exploring safe unvisited ({nx},{ny})."))
    if safe_unvisited:
        chosen_move_plan = random.choice(safe_unvisited)
        print(f"  AI Log (P2): Safe unvisited options: {[opt[0] for opt in safe_unvisited]}")
        print(f"  AI DECISION (P2): {chosen_move_plan[1]} Target: {chosen_move_plan[0]}")
        return chosen_move_plan
    else:
        print("  AI Log (P2): No safe unvisited cells found.")

    # Priority 3: Shoot a suspected Wumpus (can shoot in 8 directions)
    print(f"AI Log: Checking Priority 3 (Shoot Wumpus) - Arrows: {player_arrows}")
    if player_arrows > 0:
        shoot_candidates = []
        candidate_details = []  # For logging
        for suspect_type in ['wumpus?', 'dangerous']:
            for nx, ny in get_neighbors(player_pos, use_eight_directions=True):
                if knowledge[ny][nx] == suspect_type:
                    description = f"Shooting at {suspect_type} cell ({nx},{ny})."
                    if suspect_type == 'wumpus?':
                        shoot_candidates.append(((nx, ny), description))
                        candidate_details.append(f"({nx},{ny}) as '{suspect_type}'")
                    elif suspect_type == 'dangerous':  # More cautious with 'dangerous'
                        non_safe_options = sum(1 for nnx, nny in get_neighbors(player_pos, use_eight_directions=True) if
                                               knowledge[nny][nnx] not in ['safe', 'unknown'])
                        if non_safe_options == 1:  # Only shoot dangerous if it's the single non-safe/unknown path
                            shoot_candidates.append(((nx, ny), description))
                            candidate_details.append(f"({nx},{ny}) as '{suspect_type}' (single non-safe path)")
        if shoot_candidates:
            chosen_shot_info_tuple = random.choice(shoot_candidates)  # This is ((target_coords), description)
            target_coords = chosen_shot_info_tuple[0]
            action_description = chosen_shot_info_tuple[1]
            print(f"  AI Log (P3): Shoot candidates: {candidate_details if candidate_details else 'None'}")
            print(f"  AI DECISION (P3): {action_description} Target: {target_coords}")
            return ('shoot', target_coords, action_description)  # ('shoot', (tx,ty), description)
        else:
            print("  AI Log (P3): No suitable Wumpus suspects to shoot.")
    else:
        print("  AI Log (P3): No arrows left.")

    # Priority 4: Backtrack to a safe, visited cell (all 8 directions)
    print("AI Log: Checking Priority 4 (Backtrack to other safe visited cell)")
    safe_visited_options = []
    last_pos_option = None
    for nx, ny in get_neighbors(player_pos, use_eight_directions=True):
        if knowledge[ny][nx] == 'safe':  # Implies visited if not current cell, and not unvisited (P2)
            # Check if it was already processed by P2 (safe unvisited). If visited, it's for backtrack.
            if (nx, ny) in visited:  # Explicitly check if it's a cell we've been to before
                move_opt_tuple = ((nx, ny), f"Backtracking to safe cell ({nx},{ny}).")
                if tuple(last_player_pos or [-1, -1]) == (nx, ny):
                    last_pos_option = move_opt_tuple  # ((coords), description)
                else:
                    safe_visited_options.append(move_opt_tuple)

    if safe_visited_options:  # Prefer other safe visited cells over immediate backtrack
        chosen_move_plan = random.choice(safe_visited_options)
        print(f"  AI Log (P4): Other safe visited options: {[opt[0] for opt in safe_visited_options]}")
        print(f"  AI DECISION (P4): {chosen_move_plan[1]} Target: {chosen_move_plan[0]}")
        return chosen_move_plan
    else:
        print("  AI Log (P4): No other safe visited cells to backtrack to.")

    # Priority 5: Explore an 'unknown' cell (all 8 directions, risky)
    print("AI Log: Checking Priority 5 (Explore unknown cell)")
    unknown_options = []
    for nx, ny in get_neighbors(player_pos, use_eight_directions=True):
        if knowledge[ny][nx] == 'unknown':  # By definition, unvisited
            unknown_options.append(((nx, ny), f"Exploring unknown cell ({nx},{ny}) - Risky!"))
    if unknown_options:
        chosen_move_plan = random.choice(unknown_options)
        print(f"  AI Log (P5): Unknown cell options: {[opt[0] for opt in unknown_options]}")
        print(f"  AI DECISION (P5): {chosen_move_plan[1]} Target: {chosen_move_plan[0]}")
        return chosen_move_plan
    else:
        print("  AI Log (P5): No unknown cells to explore.")

    # Priority 6: If the only safe visited option was to go back to last_player_pos
    print("AI Log: Checking Priority 6 (Backtrack to immediate last position)")
    if last_pos_option:
        print(f"  AI DECISION (P6): {last_pos_option[1]} Target: {last_pos_option[0]}")
        return last_pos_option
    else:
        print("  AI Log (P6): No option to backtrack to immediate last position (or it wasn't safe/visited).")


    print("AI Log: Checking Priority 7 (Desperate Random Move)")
    all_adjacent_cells = get_neighbors(player_pos, use_eight_directions=True)
    if all_adjacent_cells:
        chosen_random_neighbor = random.choice(all_adjacent_cells)
        action_description = f"Desperate random move to ({chosen_random_neighbor[0]},{chosen_random_neighbor[1]})."
        print(f"  AI Log (P7): All adjacent options for random move: {all_adjacent_cells}")
        print(f"  AI DECISION (P7): {action_description} Target: {chosen_random_neighbor}")
        return (chosen_random_neighbor, action_description)
    else:

        action_description = "Critically stuck! No adjacent cells."
        print(f"  AI DECISION (P7 - Fallback): {action_description} Target: {player_pos}")
        return (tuple(player_pos), action_description)


def agent_step():
    global player_pos, player_arrows, last_player_pos, recently_cleared_wumpus_cell, display_messages_history, game_over_flag

    if game_over_flag:
        return

    update_knowledge(tuple(player_pos))

    if board[player_pos[1]][player_pos[0]] == 'G':
        if collect_gold_action():
            display_messages_history.append(f"Collected Gold at ({player_pos[0]},{player_pos[1]})!")
            game_over_text = check_game_over()
            if game_over_text and game_over_flag:
                display_messages_history.append(game_over_text)
                return

    if game_over_flag:
        return


    action_plan = choose_next_move()

    action_type = action_plan[0]

    current_action_message = action_plan[-1]

    if action_type == 'shoot':
        target_coords = action_plan[1]  # action_plan is ('shoot', (tx,ty), description)
        player_arrows -= 1
        tx, ty = target_coords

        shot_hit_wumpus_made_safe = False
        if (tx, ty) in wumpus_alive:
            wumpus_alive.remove((tx, ty))

            if board[ty][tx] != 'P':
                knowledge[ty][tx] = 'safe'
                shot_hit_wumpus_made_safe = True
            else:
                knowledge[ty][tx] = 'pit?'


        if shot_hit_wumpus_made_safe:
            recently_cleared_wumpus_cell = (tx, ty)
        else:
            recently_cleared_wumpus_cell = None

    elif isinstance(action_type, tuple) and len(action_type) == 2:
        new_px, new_py = action_type[0], action_type[1]
        if player_pos != [new_px, new_py]:
            last_player_pos = list(player_pos)
            player_pos[0], player_pos[1] = new_px, new_py

    elif action_type == 'grab_gold':
        pass


    if current_action_message and (
            not display_messages_history or display_messages_history[-1] != current_action_message):
        display_messages_history.append(current_action_message)
        if len(display_messages_history) > 3:
            display_messages_history.pop(0)

    game_over_text = check_game_over()
    if game_over_text and game_over_flag:
        display_messages_history.append(game_over_text)



def main():
    global player_pos, player_arrows, collected_gold, visited, wumpus_alive, knowledge
    global board, game_over_flag, last_player_pos, show_gold_acquired_message_timer
    global display_messages_history, recently_cleared_wumpus_cell, NUM_WUMPUS, NUM_GOLD, NUM_PITS

    board = [[' ' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    player_pos = [0, 0]
    player_arrows = NUM_WUMPUS + 1
    collected_gold = 0
    visited.clear()
    visited.add((0, 0))
    wumpus_alive.clear()
    knowledge = [['unknown' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    knowledge[0][0] = 'safe'
    recently_cleared_wumpus_cell = None

    place_objects()

    game_over_flag = False
    last_player_pos = None
    show_gold_acquired_message_timer = 0
    display_messages_history = ["Welcome to 8-Way Wumpus World!"]

    running = True
    clock = pygame.time.Clock()
    agent_action_timer = pygame.time.get_ticks()
    AGENT_ACTION_INTERVAL = 750

    while running:
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r and game_over_flag:
                    print("\n--- RESTARTING GAME ---\n")
                    main()
                    return

        if not game_over_flag and current_time - agent_action_timer > AGENT_ACTION_INTERVAL:
            agent_step()
            agent_action_timer = current_time

        screen.fill(BLACK)
        draw_grid()
        draw_objects()
        draw_messages_on_cells()
        draw_player()

        # --- Message Display Logic ---
        percept_messages = get_player_perceptions()
        # Combine last action description with current perceptions for display
        # display_messages_history contains action outcomes.

        # For Pygame display, we want concise info: last action outcome + current critical percepts
        lines_for_pygame_display = []
        if display_messages_history:
            lines_for_pygame_display.append(display_messages_history[-1])  # Last significant event/action outcome

        # Add current percepts if not redundant with last action outcome
        critical_percepts_to_show = []
        if not game_over_flag:
            for p_msg in percept_messages:
                if not any(p_msg.lower().replace(".", "") in hist_msg.lower() for hist_msg in
                           lines_for_pygame_display):  # Avoid redundancy
                    critical_percepts_to_show.append(p_msg)
            if not critical_percepts_to_show and not lines_for_pygame_display:  # If nothing else, say it's quiet
                lines_for_pygame_display.append("All seems quiet here.")
            elif critical_percepts_to_show:
                lines_for_pygame_display.extend(critical_percepts_to_show)

        # Trim to fit display
        if len(lines_for_pygame_display) > 2:
            lines_for_pygame_display = lines_for_pygame_display[-2:]

        if game_over_flag:
            final_message = display_messages_history[-1] if display_messages_history else "Game Over!"
            outcome_color = RED if "Game Over" in final_message and "Victory" not in final_message else GREEN
            draw_game_messages([final_message, "Press 'R' to Restart or ESC to Exit."], HEIGHT - 75, outcome_color)
        else:
            draw_game_messages(lines_for_pygame_display, HEIGHT - 100 + 5)

        score_text = f"Arrows: {player_arrows}  Gold: {collected_gold}/{NUM_GOLD}"
        draw_game_messages([score_text], HEIGHT - 30)

        if show_gold_acquired_message_timer > 0:
            gold_popup_font = pygame.font.SysFont(None, 60)
            text_surf = gold_popup_font.render("GOLD ACQUIRED!", True, YELLOW, BLACK)
            text_rect = text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 3))
            screen.blit(text_surf, text_rect)
            show_gold_acquired_message_timer -= 1

        pygame.display.flip()
        clock.tick(30)  # Screen refresh rate

    pygame.quit()


if __name__ == "__main__":
    main()