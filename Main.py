from ChessEngine import GameState
from Graph import Node
import os
import pygame
import time
import numpy as np

WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

DOUBLE_TO_SINGLE_LETTER = {'wP': 'P', 'wB': 'B', 'wN': 'N', 'wR': 'R', 'wQ': 'Q', 'wK': 'K', 'bP': 'p', 'bB': 'b',
                           'bN': 'n', 'bR': 'r', 'bQ': 'q', 'bK': 'k'}


def load_image():
    path = os.getcwd() + "/images"
    files_names = os.listdir(path)
    for f_name in files_names:
        IMAGES[DOUBLE_TO_SINGLE_LETTER[f_name[:-4]]] = pygame.transform.scale(pygame.image.load("images/" + f_name),
                                                                              (SQ_SIZE, SQ_SIZE))


def draw_game_state(screen, board, high_light_squares):
    colors = [pygame.Color("white"), pygame.Color("darkgrey")]
    # draw_board(screen)
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            pygame.draw.rect(screen, colors[(row + col) % 2],
                             pygame.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))
    pygame.draw.rect(screen, "#3182D2", pygame.Rect(7 * SQ_SIZE, 8 * SQ_SIZE, SQ_SIZE, SQ_SIZE * 8))

    high_light_colors = ["#B7DCFF", "#3182D2"]
    for hls in high_light_squares:
        pygame.draw.rect(screen, high_light_colors[(hls[1] + hls[0]) % 2],
                         pygame.Rect(hls[1] * SQ_SIZE, hls[0] * SQ_SIZE, SQ_SIZE, SQ_SIZE))

    for row in range(DIMENSION):
        for col in range(DIMENSION):
            if board[row, col] != "-":
                screen.blit(IMAGES[board[row, col]], pygame.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def display_win_message(message, screen):
    pygame.font.init()
    myfont = pygame.font.SysFont('Comic Sans MS', 100)
    textsurface = myfont.render(message, False, (0, 0, 0))
    screen.blit(textsurface, (SQ_SIZE * 1.2, WIDTH * 0.4))
    pygame.display.flip()
    time.sleep(3)


def init_draw():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT + SQ_SIZE))
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
    game_state = GameState()
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


def init_graph(game_state):

    """
    game_state.board = np.asarray([['r', '-', 'b', 'k', '-', 'b', '-', '-'],
                                   ['p', 'p', '-', 'p', 'p', 'p', '-', 'p'],
                                   ['-', '-', '-', '-', '-', '-', '-', 'B'],
                                   ['-', 'p', '-', 'P', 'Q', 'p', '-', '-'],
                                   ['-', 'P', '-', '-', '-', '-', '-', '-'],
                                   ['N', '-', '-', '-', '-', 'P', '-', '-'],
                                   ['P', 'P', '-', '-', '-', 'P', '-', 'P'],
                                   ['R', '-', '-', '-', 'R', '-', 'r', 'K']])
    game_state.current_player = True
    game_state.get_all_moves_and_ranks()
    game_state.clear_chess_threats()
    """

    Node.current_node = Node()
    Node.current_node.expand_graph(3, game_state)


def man_vs_machine():
    steps = 3
    screen, clock = init_draw()
    game_state = GameState()

    init_graph(game_state)
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

            code = game_state.compress_instance()
            is_changed = False
            for child in Node.current_node.childes:
                if child.code == code:
                    Node.current_node = child
                    is_changed = True
                    break
            if not is_changed:
                pass
                # raise Exception

            print("moves and ranks:", game_state.all_possible_moves_N_ranks)

            Node.current_node.expand_graph(steps, game_state)
            position, move = Node.current_node.find_best_move()
            game_state.set_last_click(position)
            game_state.do_move(move, game_state.get_move_rank(position, move))


if __name__ == "__main__":
    # main()
    man_vs_machine()
