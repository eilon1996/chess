import numpy as np
import math
import copy

WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}
PIECES_RANK = {
    'P': 1,
    'B': 3,
    'N': 3,
    'R': 5,
    'Q': 9,
    'K': math.inf,
    'p': 1,
    'b': 3,
    'n': 3,
    'r': 5,
    'q': 9,
    'k': math.inf
}

LAST_ROW = [7, 0]
FIRST_ROW = [0, 7]
DIRECTION = [1, -1]
WIN_MESSAGE = ["black_wins", "white_wins"]
INIT_BOARD = np.array([
    ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
    ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
    ['-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-'],
    ['-', '-', '-', '-', '-', '-', '-', '-'],
    ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
    ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R'],
])

ADD_PIECE_MOVES_DICT = {
    'p': lambda self, position: self.add_pawn_moves(position),
    'b': lambda self, position: self.add_bishop_moves(position),
    'n': lambda self, position: self.add_knight_moves(position),
    'r': lambda self, position: self.add_rook_moves(position),
    'q': lambda self, position: self.add_queen_moves(position),
    'k': lambda self, position: self.add_king_moves(position),
    'P': lambda self, position: self.add_pawn_moves(position),
    'B': lambda self, position: self.add_bishop_moves(position),
    'N': lambda self, position: self.add_knight_moves(position),
    'R': lambda self, position: self.add_rook_moves(position),
    'Q': lambda self, position: self.add_queen_moves(position),
    'K': lambda self, position: self.add_king_moves(position),
    '-': lambda self, position: None
}

"""
opponent and current get color and piece and return lower or upper char 
because its always get upper it will change only to lower when needed
"""
OPPONENT = lambda color, piece: piece.lower() if color else piece
CURRENT = lambda color, piece: piece if color else piece.lower()

LETTER_TO_NUM = {'-': 0, 'P': 1, 'B': 2, 'N': 3, 'R': 4, 'Q': 5, 'K': 6, 'p': 7, 'b': 8, 'n': 9, 'r': 10, 'q': 11,
                 'k': 12}
NUM_TO_LETTER = {0: '-', 1: 'P', 2: 'B', 3: 'N', 4: 'R', 5: 'Q', 6: 'K', 7: 'p', 8: 'b', 9: 'n', 10: 'r', 11: 'q',
                 12: 'k'}


class GameState:
    def __init__(self, **kwargs):
        if kwargs.get("code", None) is not None:
            self.decode_instance(kwargs["code"])
        else:

            self.score = [0, 0]
            self.board = INIT_BOARD.copy()
            self.current_player = True  # can be True for white or True for black

            # represent if the pieces were moved, [0] - black [1] - white
            self.is_castling_possible = [[True, True], [True, True]]
            self.win = [False, False]

        self.to_print = False
        self.last_click = None
        # if a piece is blocking a chess, allow it to stay only in the blocking path
        # dict {position:[possible moves], ...}
        self.king_position = None

        # a dict of tuple:list -> {current position: [(move, rank)...], ....}
        self.all_possible_moves_N_ranks = {}

        self.get_all_moves_and_ranks()
        self.clear_chess_threats()

    def generate_copy(self):
        instance_copy = GameState()

        # typically you should update the inner class with some new data, but in our case the init is always the same
        instance_copy.score = self.score.copy()
        instance_copy.board = self.board.copy()
        instance_copy.current_player = self.current_player
        instance_copy.all_possible_moves_N_ranks = copy.deepcopy(self.all_possible_moves_N_ranks)
        instance_copy.is_castling_possible = copy.deepcopy(self.is_castling_possible)
        instance_copy.win = self.win.copy()

        return instance_copy

    def restore_instance_from_pre_instance(self, previous_instance):

        # typically you should update the inner class with some new data, but in our case the init is always the same
        self.score = previous_instance.score.copy()
        self.board = previous_instance.board.copy()
        self.current_player = previous_instance.current_player
        self.last_click = previous_instance.last_click
        self.all_possible_moves_N_ranks = copy.deepcopy(previous_instance.all_possible_moves_N_ranks)
        self.is_castling_possible = copy.deepcopy(previous_instance.is_castling_possible)
        self.win = previous_instance.win.copy()

    def compress_instance(self):
        """
        there are 13 options for each cell, so if we give each options 4 bits it will be enough
        each row saved as a single integer
        score is a most 167 without a win and 200 max with win so at most we need 8 bit for each score
        score, current player and is_castling_possible will need another int
        :return: 9 length list of ints
        """
        code = [0] * 9
        for row in range(8):
            for col in range(8):
                code[row] += LETTER_TO_NUM[self.board[row, col]] << (col * 4)

        # score is a most 167 without a win and 200 max with win so at most we need 8 bit for each score
        code[8] = (self.score[False] + self.score[True] << 8) + \
                  (self.current_player << 16) + \
                  (self.is_castling_possible[False][0] << 17) + \
                  (self.is_castling_possible[False][1] << 18) + \
                  (self.is_castling_possible[True][0] << 19) + \
                  (self.is_castling_possible[True][1] << 20) + \
                  (self.win[False] << 21) + \
                  (self.win[True] << 22)

        return tuple(code)

    @staticmethod
    def __decode_board(code):
        board = np.full((8, 8), "")
        for row in range(8):
            for col in range(8):
                board[row, col] = NUM_TO_LETTER[code[row] % 2 ** 4]
                code[row] = code[row] >> 4
        return board


    def decode_instance(self, code):
        # we want to change the code in the code without changing the origin, so we create list from the tuple

        code_copy = list(code)
        self.board = np.full((8, 8), "")
        for row in range(8):
            for col in range(8):
                self.board[row, col] = NUM_TO_LETTER[code_copy[row] % 2 ** 4]
                code_copy[row] = code_copy[row] >> 4
        # 0-15 bits
        self.score = [0, 0]
        self.score[False] = code_copy[8] % 2 ** 8
        code_copy[8] = code_copy[8] >> 8
        self.score[True] = code_copy[8] % 2 ** 8
        code_copy[8] = code_copy[8] >> 8

        # 16 bit
        self.current_player = code_copy[8] % 2 == 1
        code_copy[8] = code_copy[8] >> 1

        # 17-20 bits
        self.is_castling_possible = [[0, 0], [0, 0]]
        self.is_castling_possible[False][0] = code_copy[8] % 2 == 1
        code_copy[8] = code_copy[8] >> 1
        self.is_castling_possible[False][1] = code_copy[8] % 2 == 1
        code_copy[8] = code_copy[8] >> 1
        self.is_castling_possible[True][0] = code_copy[8] % 2 == 1
        code_copy[8] = code_copy[8] >> 1
        self.is_castling_possible[True][1] = code_copy[8] % 2 == 1
        code_copy[8] = code_copy[8] >> 1

        # 21-22 bits
        self.win = [False, False]
        self.win[False] = code_copy[8] % 2 == 1
        code_copy[8] = code_copy[8] >> 1
        self.win[True] = code_copy[8] % 2 == 1

    @staticmethod
    def deduct_move(code1, code2):
        code1 = list(code1)
        code2 = list(code2)
        changes = []
        for row in range(8):
            for col in range(8):
                piece1 = code1[row] % 2 ** 4
                piece2 = code2[row] % 2 ** 4
                if piece1 != piece2:
                    changes.append([piece1, piece2, row, col])
                code1[row] = code1[row] >> 4
                code2[row] = code2[row] >> 4

        if len(changes) == 2:
            # the cell after the move need to be '-' which is 0
            if changes[0][1] == 0:
                move = [(changes[0][2], changes[0][3]), (changes[1][2], changes[1][3])]
            else:
                move = [(changes[1][2], changes[1][3]), (changes[0][2], changes[0][3])]
        else:  # castling
               # the cell before the move need to be 'K'/'k' which will be in 4 col
               move = [None, None]
               for cell in changes:
                   if cell[3] == 4:
                       move[0] = (cell[2], cell[3])
                   elif cell[3] == 2 or cell[3] == 6:
                       move[1] = (cell[2], cell[3])

        if None in move:
            raise Exception("None in move")
        return move

    def get_move_rank(self, position, move):
        for move_N_rank in self.all_possible_moves_N_ranks[position]:
            if move_N_rank[0] == move:
                return move_N_rank[1]

    @staticmethod
    def get_current_player(code):
        return code[8]//2**16 % 2

    def get_all_moves_and_ranks(self):
        self.all_possible_moves_N_ranks = {}
        for row in range(8):
            for cal in range(8):
                if self.board[(row, cal)] != '-' and \
                        self.board[(row, cal)].isupper() == self.current_player:
                    self.all_possible_moves_N_ranks[(row, cal)] = []
                    ADD_PIECE_MOVES_DICT[self.board[(row, cal)]](self, (row, cal))

    def remove_illegal_moves(self, king_illegal_moves, paths_to_blocks, must_stay_positions):

        # deal with king can eat a threat, only if it wont be eaten

        tmp_kings_moves = self.all_possible_moves_N_ranks[self.king_position]
        del self.all_possible_moves_N_ranks[self.king_position]

        if len(paths_to_blocks) == 0:
            for position in must_stay_positions:
                tmp_piece_moves = []
                for p in self.all_possible_moves_N_ranks[position]:
                    if p[0] in must_stay_positions[position]:
                        tmp_piece_moves.append(p)
                self.all_possible_moves_N_ranks[position] = tmp_piece_moves
        elif len(paths_to_blocks) >= 1:

            for i in range(len(tmp_kings_moves)):
                if tmp_kings_moves[i][1] < 0: # castling
                    king_illegal_moves.append(tmp_kings_moves[i][0])

            if len(paths_to_blocks) == 1:
                for position in self.all_possible_moves_N_ranks:
                    if must_stay_positions.get(position) is None:
                        tmp_piece_moves = []
                        for p in self.all_possible_moves_N_ranks[position]:
                            for path in paths_to_blocks:
                                if p[0] in path:
                                    tmp_piece_moves.append(p)
                        self.all_possible_moves_N_ranks[position] = tmp_piece_moves
            elif len(paths_to_blocks) >= 2:
                tmp = []
                for move in tmp_kings_moves:
                    for path in paths_to_blocks:
                        if move not in path:
                            tmp.append(move)
                            break
                tmp_kings_moves = tmp
                self.all_possible_moves_N_ranks = {}

        self.all_possible_moves_N_ranks[self.king_position] = [move_N_rank for move_N_rank in tmp_kings_moves if move_N_rank[0] not in king_illegal_moves]


    def clear_chess_threats(self):

        def check_chess_move(check_position):
            """:return:
            -1 out of boundaries
            0 empty cell
            1 own team piece
            2 opponent piece
            """
            # check if in board and the piece in the position if exist is not in the same team
            if 0 > check_position[0] or check_position[0] > 7 or 0 > check_position[1] or check_position[1] > 7:
                return -1
            piece_in_position = self.board[check_position]
            if piece_in_position == '-': return 0
            if piece_in_position.isupper() == self.current_player: return 1
            return 2

        must_stay_positions = {}
        paths_to_blocks = []

        # check if the king will be threaten in certain moves
        is_king_current_position = True
        king_positions = [self.king_position] + [move_N_rank[0] for move_N_rank in self.all_possible_moves_N_ranks[self.king_position]]
        king_illegal_moves = []
        for position in king_positions:
            directions = [(1, 1), (-1, 1), (1, -1), (-1, -1), (0, 1), (0, -1), (1, 0), (-1, 0)]
            for d in directions:
                blocker = None
                for i in range(1, 8):
                    new_position = (position[0] + i * d[0], position[1] + i * d[1])
                    status = check_chess_move(new_position)
                    if status == -1:
                        break
                    elif status == 0:
                        pass
                    elif status == 1:
                        if is_king_current_position:
                            if blocker is not None: break  # there is no threat from this direction
                            blocker = new_position
                        else:
                            break
                    elif status == 2:
                        piece = self.board[new_position]
                        is_threaten = False
                        if i == 1 and piece in "kK": is_threaten = True
                        if d[0] * d[1] == 0:
                            if piece in "rRqQ": is_threaten = True
                        elif piece in "bBqQ":
                            is_threaten = True
                        if is_threaten:
                            if is_king_current_position:
                                if blocker is None:
                                    paths_to_blocks.append([(position[0] + j * d[0], position[1] + j * d[1]) for j in range(1, i + 1)])
                                    # might add out of boundaries illegal move but its ok
                                    if i == 1:  # to eat the piece will be legal move
                                        king_illegal_moves.append((position[0] - d[0], position[1] - d[1]))
                                    else:
                                        king_illegal_moves.extend([(position[0] + d[0], position[1] + d[1]),
                                                                   (position[0] - d[0], position[1] - d[1])])
                                else:  # len(blocker) == 1:
                                    must_stay_positions[blocker] = [
                                        (position[0] + j * d[0], position[1] + j * d[1]) for j in range(1, i + 1)]
                                break
                            else:
                                king_illegal_moves.append(position)
                        else:
                            break

            for i in [-1, 1]:
                new_position = (position[0] + DIRECTION[self.current_player], position[1] + i)
                if 0 > new_position[0] or new_position[0] > 7 or 0 > new_position[1] or new_position[1] > 7: continue
                if self.board[new_position] == OPPONENT(self.current_player, "P"):
                    if is_king_current_position:
                        paths_to_blocks.append([new_position])
                    else:
                        king_illegal_moves.append(position)

            knight_options = [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]
            for i in knight_options:
                new_position = (position[0] + i[0], position[1] + i[1])
                if 0 > new_position[0] or new_position[0] > 7 or 0 > new_position[1] or new_position[1] > 7: continue
                if self.board[new_position] == OPPONENT(self.current_player, "N"):
                    if is_king_current_position:
                        paths_to_blocks.append([new_position])
                    else:
                        king_illegal_moves.append(position)

            # only in the first time it the king real position, the other are possible moves
            is_king_current_position = False

        self.remove_illegal_moves(king_illegal_moves,paths_to_blocks, must_stay_positions)

    def get_players_pieces(self, board=None):
        if board is None: board = self.board
        players_pieces = {True: [], False: []}
        for i in range(8):
            for j in range(8):
                piece = board[i, j]
                if piece != '-':
                    players_pieces[piece.isupper()].append([piece.upper(), (i, j)])
        return players_pieces

    def check_and_add_move(self, position, new_position):
        """
        check if the new possition is valid, if so add it to the optionals moves, handle eat move
        :return:
        """
        # check if in board and the piece in the position if exist is not in the same team
        if 0 <= new_position[0] <= 7 and 0 <= new_position[1] <= 7:
            piece_in_position = self.board[new_position]
            if piece_in_position == '-':
                self.all_possible_moves_N_ranks[position].append((new_position, 0))  # a valid move
                return True  # valid move, return True to keep the loop
            if piece_in_position.isupper() != self.current_player:
                self.all_possible_moves_N_ranks[position].append((new_position, PIECES_RANK[piece_in_position]))  # valid move# eat move
                # a valid move but cant continue the loop, return False to break from the loop
        return False  # not a valid move, return False to break from the loop

    def add_bishop_moves(self, position):
        directions = [(1, 1), (-1, 1), (1, -1), (-1, -1)]
        for d in directions:
            for i in range(1, 8):
                new_position = (position[0] + i * d[0], position[1] + i * d[1])
                # if the move is not possible, there is no any farther move in this direction is not possible
                if not self.check_and_add_move(position, new_position): break

    def add_rook_moves(self, position):
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for d in directions:
            for i in range(1, 8):
                new_position = (position[0] + i * d[0], position[1] + i * d[1])
                if not self.check_and_add_move(position, new_position): break

    def add_queen_moves(self, position):
        self.add_bishop_moves(position)
        self.add_rook_moves(position)

    def add_pawn_moves(self, position):
        color = self.current_player

        # check for Promotion (pawn become a queen)
        if position[0] == LAST_ROW[color] - DIRECTION[color]:
            rank = 8  # you get a queen (9) but loose a pawn (1)
        else:
            rank = 0

        if position[0] * DIRECTION[color] < LAST_ROW[color] * DIRECTION[color]:  # check if is in limit by color
            if self.board[(position[0] + DIRECTION[color], position[1])] == '-':
                self.all_possible_moves_N_ranks[position].append(((position[0] + DIRECTION[color], position[1]), rank))
                if position[0] == FIRST_ROW[color] + DIRECTION[color] and self.board[
                    (position[0] + DIRECTION[color] * 2, position[1])] == '-':
                    self.all_possible_moves_N_ranks[position].append(
                        ((position[0] + DIRECTION[color] * 2, position[1]), rank))
            # check for eat move
            if position[1] > 0 and self.board[(position[0] + DIRECTION[color], position[1] - 1)] != '-' \
                    and self.board[(position[0] + DIRECTION[color], position[1] - 1)].isupper() != color:

                self.all_possible_moves_N_ranks[position].append(((position[0] + DIRECTION[color], position[1] - 1),
                                    rank + PIECES_RANK[self.board[(position[0] + DIRECTION[color], position[1] - 1)]]))

            if position[1] < 7 and self.board[(position[0] + DIRECTION[color], position[1] + 1)][0] != '-' \
                    and self.board[(position[0] + DIRECTION[color], position[1] + 1)].isupper() != color:
                self.all_possible_moves_N_ranks[position].append((
                    (position[0] + DIRECTION[color], position[1] + 1),
                    rank + PIECES_RANK[self.board[(position[0] + DIRECTION[color], position[1] + 1)]]))

    def add_knight_moves(self, position):
        knight_options = [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]
        for option in knight_options:
            new_position = (option[0] + position[0], option[1] + position[1])
            self.check_and_add_move(position, new_position)

    def add_king_moves(self, position):
        # because castling will never be an eat move, we will mark it with a negative rank -10 for left, -11 for right
        self.king_position = position
        king_options = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]
        for option in king_options:
            new_position = (option[0] + position[0], option[1] + position[1])
            self.check_and_add_move(position, new_position)

        if self.current_player:
            row = 7
        else:
            row = 0
        if self.is_castling_possible[self.current_player][0] and \
                self.board[(row, 3)] == '-' and self.board[(row, 2)] == '-' and \
                self.board[(row, 1)] == '-':
            self.all_possible_moves_N_ranks[position].append(((row, 2), -10))
        if self.is_castling_possible[self.current_player][0] and \
                self.board[(row, 5)] == '-' and self.board[(row, 6)] == '-':
            self.all_possible_moves_N_ranks[position].append(((row, 6), -11))

    def handle_castling(self, rank):
        if self.current_player:
            # execute castling
            if rank == -10:
                self.is_castling_possible[True] = [False, False]
                self.board[(7, 3)] = "R"
                self.board[(7, 0)] = '-'
            elif rank == -11:
                self.is_castling_possible[True] = [False, False]
                self.board[(7, 5)] = "R"
                self.board[(7, 7)] = '-'

            # disable castling
            elif self.last_click == (7, 0):
                self.is_castling_possible[True][0] = False
            elif self.last_click == (7, 7):
                self.is_castling_possible[True][1] = False
            elif self.last_click == (7, 4):
                self.is_castling_possible[True][0] = False
                self.is_castling_possible[True][1] = False
        else:
            # execute castling
            if rank == -10:
                self.is_castling_possible[False] = [False, False]
                self.board[(0, 3)] = "r"
                self.board[(0, 0)] = '-'
            elif rank == -11:
                self.is_castling_possible[False] = [False, False]
                self.board[(0, 5)] = "r"
                self.board[(0, 7)] = '-'
            # disable castling
            elif self.last_click == (0, 0):
                self.is_castling_possible[False][0] = False
            elif self.last_click == (0, 7):
                self.is_castling_possible[False][1] = False
            elif self.last_click == (0, 4):
                self.is_castling_possible[False][0] = False
                self.is_castling_possible[False][1] = False

    def check_if_can_move(self):
        can_move = False
        for position in self.all_possible_moves_N_ranks:
            if len(self.all_possible_moves_N_ranks[position]) > 0:
                return None  # no one won yet

        # the board is printed for the record
        # if player won, we will print the board without the ';' for creating the test easier
        if not can_move:
            self.win[not self.current_player] = True
            if self.to_print:
                print(WIN_MESSAGE[not self.current_player] + ";")
            return WIN_MESSAGE[not self.current_player]

    def do_move(self, current_click, rank):
        if rank > 0:
            # update player score
            self.score[self.current_player] += rank

        # update board
        self.board[current_click] = self.board[self.last_click]
        self.board[self.last_click] = '-'
        self.handle_castling(rank)

        # handle queening, check by possible
        if rank in [8, 11, 13, 17]:
            self.board[current_click] = CURRENT(self.current_player, 'Q')
        # game over for one of the sides
        if rank == math.inf:
            raise Exception("king was eaten")
            return WIN_MESSAGE[self.current_player]

        if self.to_print:
            # print for record
            print(str(self.board) + ";")

        return self.prepare_for_next_move()

    def prepare_for_next_move(self):
        # prepare for the next move
        self.current_player = not self.current_player
        self.last_click = None
        self.all_possible_moves_N_ranks.clear()
        self.get_all_moves_and_ranks()
        self.clear_chess_threats()

        return self.check_if_can_move()


    def set_last_click(self, click):
        if self.board[click] == '-':
            raise Exception("click on empty cell")
        self.last_click = click

    def handle_mouse_click(self, mouse_location):
        if self.to_print:
            # print for record
            print(str(mouse_location) + ";")
        current_click = (
            mouse_location[1] // SQ_SIZE, mouse_location[0] // SQ_SIZE)  # we switch the place to match the array
        if current_click[0] == 8:
            return "goodbye"
        piece = self.board[current_click]
        if self.last_click is None:
            if piece != '-' and piece.isupper() == self.current_player:
                self.set_last_click(current_click)
        else:
            if current_click == self.last_click:
                self.last_click = None

            else:
                for move_N_rank in self.all_possible_moves_N_ranks[self.last_click]:
                    if current_click == move_N_rank[0]:
                        self.last_move = (self.last_click, current_click)
                        return self.do_move(current_click, move_N_rank[1])

                # if not found
                if current_click in self.all_possible_moves_N_ranks.keys():
                    self.set_last_click(current_click)

    def get_highlight_squares(self):
        if self.last_click is None: return []  # if there is no last click there aren't any possible moves
        return [self.last_click] + [move_N_rank[0] for move_N_rank in self.all_possible_moves_N_ranks[self.last_click]]
