import random
import time
from ChessEngine import GameState

INIT_CODE = (2844571802, 2004318071, 0, 0, 0, 0, 286331153, 1126584884, 2031616)
INIT_SCORE = -10**6

class Node:
    # {code: Node,...}
    dict_of_nodes = {}
    # {code: [is_visited, calculated_score],...}
    visit_score_dict = {}

    current_node = None

    def __init__(self, game_state=None, code=INIT_CODE):
        """
        only one param will be given
        """
        if game_state is None:
            self.code = code
            self.score = [code[8] % 2 ** 8, code[8] // (2 ** 8) % 2 ** 8]
            self.win = code[8] // (2 ** 21) % 2 ** 2 > 0
        else:
            self.code = code
            self.score = game_state.score  # the current move score
            self.win = game_state.win[False] or game_state.win[True]

        self.childes = []
        self.visited = False
        self.calculated_score = -1
        if Node.dict_of_nodes.get(self.code, None) is None:
            Node.dict_of_nodes[self.code] = self
        else:
            raise Exception("Node already exist")

    def add_child(self, child=None):
        if isinstance(child, GameState):
            child = Node(child)
        self.childes.append(child)
        return child

    def expand_graph_not_from_leaf(self, steps):
        if steps == 0:
            return
        if len(self.childes) == 0:
            game_state = GameState(code=self.code)
            self.expand_graph(steps, game_state)

        for child in self.childes:
            if Node.dict_of_nodes.get(child.code, None) is None:
                raise Exception
            if not child.win:  # if this move is not a win move then further check
                child.expand_graph_not_from_leaf(steps - 1)

    def count_reachable_nodes(self, compare=True):
        self.visited = compare
        if len(self.childes) == 0:
            return 1

        counter = 1
        for child in self.childes:
            if child.visited != compare:
                counter += child.count_reachable_nodes(compare)
        return counter

    def __count_reachable_nodes_tree(self, dict_nodes):
        dict_nodes[self.code] = self
        counter = 1
        for child in self.childes:
            counter += child.__count_reachable_nodes_tree(dict_nodes)
        return counter

    def count_reachable_nodes_tree(self):
        dict_of_nodes = {}
        counter = self.__count_reachable_nodes_tree(dict_of_nodes)
        print("total nodes:", counter)
        print("different nodes:", len(dict_of_nodes))

    def expand_tree_with_duplicates(self, steps, game_state):
        """
        run only on the first step options and call in each step to expand_tree_rec()
        :return: recomanded step for best resulte
        """
        if steps <= 0:
            return

        if game_state.win[0] or game_state.win[1]:
            raise Exception

        copy_instance = game_state.generate_copy()

        for position in copy_instance.all_possible_moves_N_ranks:
            for move in copy_instance.all_possible_moves_N_ranks[position]:
                game_state.set_last_click(position)
                res = game_state.do_move(move)

                if res is not None:
                    self.add_child(game_state)

                else:
                    child = self.add_child(game_state)
                    child.expand_tree_with_duplicates(steps - 1, game_state)

                game_state.restore_instance_from_pre_instance(copy_instance)

    def expand_graph(self, steps, game_state):
        """
        run only on the first step options and call in each step to expand_tree_rec()
        :return: recomanded step for best resulte
        """

        if steps <= 0 or (game_state.win[0] or game_state.win[1]):
            return

        if len(self.childes) > 0:
            for child in self.childes:
                child.expand_graph(steps - 1, GameState(code=child.code))

        else:
            copy_instance = game_state.generate_copy()

            for position in copy_instance.all_possible_moves_N_ranks:
                for move, rank in copy_instance.all_possible_moves_N_ranks[position]:
                    game_state.set_last_click(position)
                    game_state.do_move(move, rank)

                    code = game_state.compress_instance()
                    if Node.dict_of_nodes.get(code) is None:
                        child = Node(game_state, code)
                    else:
                        child = Node.dict_of_nodes[code]

                    self.add_child(child)
                    child.expand_graph(steps - 1, game_state)

                    game_state.restore_instance_from_pre_instance(copy_instance)

    def calculated_score_worst_case(self):
        """
        we guess that the opponent will take the best move for him for the long run
        we subtract the opponent best score from this move score to check the worthwhileness of the move
        note that basically what it does is: calculated_score = score - opponent_best_move_score + my_move - opponent...
        """
        max_score = 0
        for child in self.childes:
            if child.calculated_score > max_score:
                max_score = child.calculated_score
        self.calculated_score = self.score - max_score

    def __find_best_move_avg(self, start_depth, current_depth, avg_n=3, player=True):
        if len(self.childes) == 0:
            calculated_score = self.score[player] - self.score[not player]
            Node.visit_score_dict[self.code] = [True, calculated_score]
            return calculated_score
        if Node.visit_score_dict[self.code][0]:
            if Node.visit_score_dict[self.code][1] == INIT_SCORE:
                Node.visit_score_dict[self.code][1] = self.score
            return Node.visit_score_dict[self.code][1]

        Node.visit_score_dict[self.code][0] = True

        if start_depth - current_depth % 2 == 0:
            max_score = INIT_SCORE
            for child in self.childes:
                tmp_score = Node.__find_best_move_avg(child, start_depth, current_depth + 1, avg_n, player)
                if tmp_score > max_score:
                    max_score = tmp_score
            Node.visit_score_dict[self.code][1] = max_score
            return Node.visit_score_dict[self.code][1]

        else:
            scores = []
            for child in self.childes:
                scores.append(Node.__find_best_move_avg(child, start_depth, current_depth + 1, avg_n, player))
            scores.sort()
            Node.visit_score_dict[self.code][1] = sum(scores[:avg_n]) / avg_n
            return Node.visit_score_dict[self.code][1]

    def __find_best_move(self, start_depth, current_depth, avg_n=3, player=True):
        if len(self.childes) == 0:
            calculated_score = self.score[player] - self.score[not player]
            Node.visit_score_dict[self.code] = [True, calculated_score]
            return calculated_score
        if Node.visit_score_dict[self.code][0]:
            if Node.visit_score_dict[self.code][1] == INIT_SCORE:
                Node.visit_score_dict[self.code][1] = self.score
            return Node.visit_score_dict[self.code][1]

        Node.visit_score_dict[self.code][0] = True

        if start_depth - current_depth % 2 == 0:
            max_score = INIT_SCORE
            for child in self.childes:
                tmp_score = Node.__find_best_move(child, start_depth, current_depth + 1, avg_n, player)
                if tmp_score > max_score:
                    max_score = tmp_score
            Node.visit_score_dict[self.code][1] = max_score
            return Node.visit_score_dict[self.code][1]

        else:
            min_score = -INIT_SCORE
            for child in self.childes:
                tmp_score = Node.__find_best_move(child, start_depth, current_depth + 1, avg_n, player)
                if tmp_score < min_score:
                    min_score = tmp_score
            Node.visit_score_dict[self.code][1] = min_score
            return Node.visit_score_dict[self.code][1]


    def find_best_move(self):
        """
        run DFS until reach to bottom
        on the way up choose the score base on:
            if current player - best score
            if opponent - avg of top 3
        """
        Node.visit_score_dict = {code: [False, -1] for code in Node.dict_of_nodes}
        avg_n = 2
        max_score = INIT_SCORE
        max_childes = []
        for child in self.childes:
            tmp_score = child.__find_best_move_avg(0, 1, avg_n, GameState.get_current_player(self.code))
            # tmp_score = child.__find_best_move(0, 1, avg_n, GameState.get_current_player(self.code))
            if tmp_score > max_score:
                max_score = tmp_score
                max_childes = [child]
            elif tmp_score == max_score:
                max_childes.append(child)

        # choose randomly a child and get its move
        print("best", max_score, [GameState.deduct_move(self.code, c.code) for c in max_childes])
        Node.current_node = random.choice(max_childes)
        return GameState.deduct_move(self.code, Node.current_node.code)

    @staticmethod
    def save_graph(file_name):
        nodes_key = list(Node.dict_of_nodes.keys())
        nodes_key.sort()
        code_to_index = {nodes_key[i]: i for i in range(len(nodes_key))}
        # turn the childes nodes into an indexes list to be the value in the dict  {code:[childes index,...], ...}
        edges_dict = {k: [code_to_index[child.code] for child in Node.dict_of_nodes[k].childes] for k in nodes_key}
        with open('graphs/' + file_name + '.txt', 'w') as file:
            file.write(str(edges_dict))
            file.close()

    @staticmethod
    def restore_graph(file_name):
        with open('graphs/' + file_name + '.txt', 'r') as file:
            edges_dict = eval(file.read())
            file.close()
        nodes_codes = list(edges_dict.keys())
        Node.dict_of_nodes = {code: Node(code=code) for code in nodes_codes}
        for code in nodes_codes:
            # match the childes index to nodes from the dict
            Node.dict_of_nodes[code].childes = [Node.dict_of_nodes[nodes_codes[index]] for index in edges_dict[code]]

        return Node.dict_of_nodes[INIT_CODE]  # return root

    """    
    def __str__(self):
        return str(self.score)

    def __repr__(self):
        return "num of childs: " + str(len(self.childes))
    """


def test1(steps):
    gs = GameState()
    root = Node(gs)
    s = time.time()
    root.expand_tree_with_duplicates(steps, gs)
    print(time.time() - s)
    root.count_reachable_nodes_tree()
    print(root.find_best_move())
    print()
    """
    4 steps: 
    count before delete: 206604
    count after delete:  77570
    dict length:         77570

    5
    count after delete:  895488

    """


def test2(steps):
    gs = GameState()
    root = Node(gs)
    s = time.time()
    dict_of_nodes = root.expand_graph(steps, gs)
    print(time.time() - s)

    print(root.count_reachable_nodes())
    print(root.find_best_move())
    print()
    """
    3:
    5783

    4 steps: 
    time: 110
    count before delete: 77570
    dict length:         77570

    5
    686.14
    895488
    895488
    """


def test3(steps):
    root = Node.restore_graph(str(steps) + "_steps")
    print(root.count_reachable_nodes())
    print(root.find_best_move())
    print()


if __name__ == '__main__':
    steps = 4
    # test1(steps)
    test2(steps)
    # test3(steps)
    # Node.save_graph(str(steps)+"_steps")
    # root = Node.restore_graph(str(steps)+"_steps")
    print("A")
