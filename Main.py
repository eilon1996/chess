from ChessEngine import GameState
from Graph import Node
from firebase import Firebase
import os
import pygame
import time


class Game:
    WIDTH = HEIGHT = 512
    DIMENSION = 8
    SQ_SIZE = HEIGHT // DIMENSION
    MAX_FPS = 15
    PIECE_SIZE = (SQ_SIZE, SQ_SIZE)
    MASS_WIDTH = 300
    MASS_HEIGHT = 150
    MASS_LEFT = WIDTH/2-MASS_WIDTH/2
    MASS_TOP = HEIGHT/2-MASS_HEIGHT/2

    MASSAGE_SIZE = (300, 150)
    IMAGES = {}

    SQUARE_IMAGES_DICT = {'wP': 'P', 'wB': 'B', 'wN': 'N', 'wR': 'R', 'wQ': 'Q', 'wK': 'K', 'bP': 'p', 'bB': 'b',
                          'bN': 'n', 'bR': 'r', 'bQ': 'q', 'bK': 'k', 'exit': 'exit'}

    HIGH_LIGHT_COLORS = ["#B7DCFF", "#3182D2"]
    COLORS = [pygame.Color("white"), pygame.Color("darkgrey")]

    MASS_IMG_RATIO = 300/500
    CHOICE_BOXES = [pygame.Rect(MASS_LEFT + 15 *MASS_IMG_RATIO, MASS_TOP + 88*MASS_IMG_RATIO, (240-15)*MASS_IMG_RATIO, (200-88)*MASS_IMG_RATIO),
                    pygame.Rect(MASS_LEFT + 240 *MASS_IMG_RATIO, MASS_TOP + 88*MASS_IMG_RATIO, (240-15)*MASS_IMG_RATIO, (200-88)*MASS_IMG_RATIO)]

    COMPUTE_DEEP_STEPS = 3


    def __init__(self):

        print()  # this is important for the tests
        self.game_state = GameState()
        self.screen, self.clock = Game.init_draw()

        Game.init_draw()

        ### choose_against_who_to_play and choose color

        self.display_massage("play_against")
        if self.pygame_loop(Game.__choose, False):
            self.game_state.get_all_moves_and_ranks()
            self.play_against = "other_player"

            self.display_massage("choose_room")
            create_or_join = self.pygame_loop(Game.__choose, False)  # create = 0, join = 1
            if create_or_join:
                self.create_room()
            else:
                self.join_room()


        else:  # right square
            self.my_color = self.choose_color()
            Node.current_node = Node()
            Node.current_node.expand_graph(Game.COMPUTE_DEEP_STEPS, self.game_state)
            print("computer")
            self.play_against = "computer"


    @staticmethod
    def init_draw():
        pygame.init()
        screen = pygame.display.set_mode((Game.WIDTH, Game.HEIGHT + Game.SQ_SIZE))
        clock = pygame.time.Clock()
        screen.fill(pygame.Color("white"))
        Game.load_image()
        return screen, clock

    @staticmethod
    def load_image():
        path = os.getcwd()
        if '/' in path:
            separate = '/'
        elif '\\' in path:
            separate = '\\'
        elif '\\\\' in path:
            separate = '\\\\'
        path_list = path.split(separate)
        if path_list[-1] == 'dist':
            del path_list[-1]
            dots = '..'
        else:
            dots = '.'
        path = separate.join(path_list)
        path += separate + "images"
        print(path)
        files_names = os.listdir(path)
        for f_name in files_names:
            if Game.SQUARE_IMAGES_DICT.get(f_name[:-4]) is not None or 'exit' in f_name:
                Game.IMAGES[Game.SQUARE_IMAGES_DICT[f_name[:-4]]] = pygame.transform.scale(
                    pygame.image.load(dots + separate + "images" + separate + f_name), Game.PIECE_SIZE)
            else:
                Game.IMAGES[f_name[:-4]] = pygame.transform.scale(
                    pygame.image.load(dots + separate + "images" + separate + f_name), Game.MASSAGE_SIZE)


    @staticmethod
    def __choose(event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if Game.CHOICE_BOXES[0].collidepoint(event.pos):
                return 0  # "left"
            elif Game.CHOICE_BOXES[1].collidepoint(event.pos):
                return 1  # "right"
        return None

    def goodbye(self):
        self.display_massage("goodbye")
        time.sleep(2)

    def pygame_loop(self, function, display=True):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or \
                        (event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pos()[1] // 64 == 8):
                    self.goodbye()
                    return

                res = function(event)
                if res == "goodbye":
                    self.goodbye()
                    return

                if res is not None:
                    return res

            if display:
                self.draw_game_state()

    def display_massage(self, message):
        self.screen.blit(Game.IMAGES[message],
                         pygame.Rect(Game.MASS_LEFT, Game.MASS_TOP, Game.MASS_WIDTH, Game.MASS_HEIGHT))
        pygame.display.flip()

    def choose_color(self):
        self.display_massage("choose_color")
        return int(not self.pygame_loop(Game.__choose, False))

    def create_room(self):
        error = ""
        while True:
            room_id = self.enter_room_id(error)
            exist = Firebase.is_room_exist(room_id)
            if exist:
                self.room_id = room_id
                self.firebase = Firebase(room_id, 0)
                self.firebase.join_room()
                self.my_color = self.firebase.get_my_color()
                return
            else:
                error = "room is not exist"


    def join_room(self):
        error = ""
        while True:
            room_id = self.enter_room_id(error)
            exist = Firebase.is_room_exist(room_id)
            if exist:
                error = "room already exist"
            else:
                self.room_id = room_id
                self.my_color = self.choose_color()
                self.firebase = Firebase(room_id, 1, self.my_color)
                self.firebase.create_room()
                self.display_massage("wait_for_opponent")
                self.firebase.wait_for_opponent_to_connect()
                return


    def enter_room_id(self, error):
        font = pygame.font.Font(None, 32)
        input_box = pygame.Rect(Game.MASS_LEFT, Game.MASS_TOP, Game.MASS_WIDTH, Game.MASS_HEIGHT / 4)
        color = Game.HIGH_LIGHT_COLORS[0]
        text = ''

        while True:
            wrong_input = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise Exception("quit")

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if len(text) > 0:
                            print(text)
                            self.screen.fill(pygame.Color("white"))
                            return text
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    elif len(text) <= 6 and (event.unicode.isalpha() or event.unicode.isdigit()):
                        text += event.unicode
                    elif event.key not in [pygame.K_CAPSLOCK, pygame.K_RSHIFT,  pygame.K_LSHIFT, pygame.K_RALT,
                                           pygame.K_LALT, pygame.K_RCTRL, pygame.K_LCTRL, pygame.K_DELETE,
                                           pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN]:

                        wrong_input = True
                    error = ""

            if wrong_input:
                self.screen.fill(pygame.Color("white"))
                txt_surface = font.render("enter room id (up to 6 letters)", True, color)
                self.screen.blit(txt_surface, (input_box.x, input_box.y - Game.MASS_HEIGHT / 4))
                txt_surface = font.render(text, True, pygame.Color("red"))
                self.screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
                pygame.draw.rect(self.screen, pygame.Color("red"), input_box, 2)

                pygame.display.flip()
                self.clock.tick(Game.MAX_FPS)
                time.sleep(0.2)


            # Render the current text.
            self.screen.fill(pygame.Color("white"))
            txt_surface = font.render("enter room id (up to 6 letters)", True, color)
            self.screen.blit(txt_surface, (input_box.x, input_box.y - Game.MASS_HEIGHT / 4))
            txt_surface = font.render(text, True, color)
            self.screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
            pygame.draw.rect(self.screen, color, input_box, 2)
            if len(error) > 0:
                txt_surface = font.render(error, True, pygame.Color("red"))
                self.screen.blit(txt_surface, (input_box.x + 5, input_box.y + Game.MASS_HEIGHT / 4))

            pygame.display.flip()
            self.clock.tick(Game.MAX_FPS)


    def draw_game_state(self):
        # draw_board(screen)
        for row in range(Game.DIMENSION):
            for col in range(Game.DIMENSION):
                pygame.draw.rect(self.screen, Game.COLORS[(row + col) % 2],
                                 pygame.Rect(col * Game.SQ_SIZE, row * Game.SQ_SIZE, Game.SQ_SIZE, Game.SQ_SIZE))

        high_light_squares = self.game_state.get_highlight_squares()
        for hls in high_light_squares:
            pygame.draw.rect(self.screen, Game.HIGH_LIGHT_COLORS[(hls[1] + hls[0]) % 2],
                             pygame.Rect(hls[1] * Game.SQ_SIZE, hls[0] * Game.SQ_SIZE, Game.SQ_SIZE, Game.SQ_SIZE))

        for row in range(Game.DIMENSION):
            for col in range(Game.DIMENSION):
                if self.game_state.board[row, col] != "-":
                    self.screen.blit(Game.IMAGES[self.game_state.board[row, col]],
                                     pygame.Rect(col * Game.SQ_SIZE, row * Game.SQ_SIZE, Game.SQ_SIZE, Game.SQ_SIZE))

        self.screen.blit(Game.IMAGES['exit'],
                         pygame.Rect(7 * Game.SQ_SIZE, 8 * Game.SQ_SIZE, Game.SQ_SIZE, Game.SQ_SIZE))

        self.clock.tick(Game.MAX_FPS)
        pygame.display.flip()

    def play(self):
        if self.play_against == "computer":
            self.pygame_loop(self.__play_against_the_computer)
        else:
            self.pygame_loop(self.__play_against_other_player)

    def __play_against_other_player_same_computer(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_location = pygame.mouse.get_pos()
            return_value = self.game_state.handle_mouse_click(mouse_location)
            if return_value is not None:
                return "goodbye"

    def __play_against_other_player(self, event):
        return_value = None
        if self.game_state.current_player == self.my_color:  # player turn
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_location = pygame.mouse.get_pos()
                return_value = self.game_state.handle_mouse_click(mouse_location)

                if self.game_state.current_player != self.my_color: # when player is changed
                    self.firebase.set_last_move(self.game_state.last_move)

        else:  # opponent turn
            last_move = self.firebase.get_last_move()
            if last_move != self.firebase.last_move:
                position, move = (int(last_move[0]), int(last_move[1])), (int(last_move[2]), int(last_move[3]))
                self.game_state.set_last_click(position)
                return_value = self.game_state.do_move(move, self.game_state.get_move_rank(position, move))

        if return_value is not None:
            self.display_massage(return_value)
            time.sleep(2)
            return "goodbye"



    def __play_against_the_computer(self, event):
        return_value = None

        if self.game_state.current_player == self.my_color:  # player turn
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_location = pygame.mouse.get_pos()
                return_value = self.game_state.handle_mouse_click(mouse_location)

        else:  # computer turn
            code = self.game_state.compress_instance()
            for child in Node.current_node.childes:
                if child.code == code:
                    Node.current_node = child
                    break
            # print("moves and ranks:", self.game_state.all_possible_moves_N_ranks)

            Node.current_node.expand_graph(Game.COMPUTE_DEEP_STEPS, self.game_state)
            position, move = Node.current_node.find_best_move()
            self.game_state.set_last_click(position)
            return_value = self.game_state.do_move(move, self.game_state.get_move_rank(position, move))

        if return_value is not None:
            self.display_massage(return_value)
            time.sleep(2)
            return "goodbye"


if __name__ == "__main__":
    game = Game()
    game.play()