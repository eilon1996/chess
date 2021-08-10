import ChessEngine as ChessEngine
import best_move
import os
import pygame
import time


WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT//DIMENSION
MAX_FPS = 15
IMAGES = {}

DOUBLE_TO_SINGLE_LETTER = {'wP': 'P', 'wB': 'B', 'wN': 'N', 'wR': 'R', 'wQ': 'Q', 'wK': 'K', 'bP': 'p', 'bB': 'b', 'bN': 'n', 'bR': 'r', 'bQ': 'q',
                 'bK': 'k'}


def load_image():
    path = os.getcwd() + "/images"
    files_names = os.listdir(path)
    for f_name in files_names:
        IMAGES[DOUBLE_TO_SINGLE_LETTER[f_name[:-4]]] = pygame.transform.scale(pygame.image.load("images/"+f_name), (SQ_SIZE, SQ_SIZE))


def draw_game_state(screen, board, high_light_squares):
    colors = [pygame.Color("white"), pygame.Color("darkgrey")]
    #draw_board(screen)
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            pygame.draw.rect(screen, colors[(row+col)%2], pygame.Rect(col*SQ_SIZE, row*SQ_SIZE, SQ_SIZE, SQ_SIZE))
    pygame.draw.rect(screen, "#3182D2", pygame.Rect(7*SQ_SIZE, 8 * SQ_SIZE, SQ_SIZE, SQ_SIZE*8))

    high_light_colors = ["#B7DCFF", "#3182D2"]
    for hls in high_light_squares:
        pygame.draw.rect(screen, high_light_colors[(hls[1]+hls[0]) % 2], pygame.Rect(hls[1] * SQ_SIZE, hls[0] * SQ_SIZE, SQ_SIZE, SQ_SIZE))

    for row in range(DIMENSION):
        for col in range(DIMENSION):
            if board[row, col] != "-":
                screen.blit(IMAGES[board[row, col]], pygame.Rect(col*SQ_SIZE, row*SQ_SIZE, SQ_SIZE, SQ_SIZE))


def display_win_message(message, screen):
    pygame.font.init()
    myfont = pygame.font.SysFont('Comic Sans MS', 100)
    textsurface = myfont.render(message, False, (0, 0, 0))
    screen.blit(textsurface, (SQ_SIZE*1.2, WIDTH*0.4))
    pygame.display.flip()
    time.sleep(3)


def init_draw():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT+SQ_SIZE))
    clock = pygame.time.Clock()
    screen.fill(pygame.Color("white"))
    load_image()
    return screen, clock
    # running = True


def redraw(game_state, screen, clock):
    draw_game_state(screen, game_state.board, game_state.get_highlight_squares())
    clock.tick(MAX_FPS)
    pygame.display.flip()


def main():
    print()  # this is important for the tests
    screen, clock = init_draw()
    game_state = ChessEngine.GameState()
    # need to be done separately only in the first time, later will be activate in the end of every move
    game_state.get_all_moves_and_ranks()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_location = pygame.mouse.get_pos()
                return_value = game_state.handle_mouse_click(mouse_location)
                if return_value is not None:
                    running = False
                    display_win_message(return_value, screen)
        redraw(game_state, screen, clock)


def man_vs_machine():
    screen, clock = init_draw()
    game_state = ChessEngine.GameState()
    # need to be done separately only in the first time, later will be activate in the end of every move
    game_state.get_all_moves_and_ranks()
    running = True

    while running:
        if game_state.current_player:  # player turn
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_location = pygame.mouse.get_pos()
                    return_value = game_state.handle_mouse_click(mouse_location)
                    if return_value is not None:
                        running = False
                        display_win_message(return_value, screen)
            redraw(game_state, screen, clock)
        else:  # computer turn
            position, move = best_move.find_best_move(3, game_state)
            game_state.set_last_click(position)
            game_state.do_move(move)


if __name__ == "__main__":
    "the computer can eat with the king and get killed"
    main()
    # man_vs_machine()