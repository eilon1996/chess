import random
import sys
import time

import numpy as np

from collections import deque
import ChessEngine



class Node():

    def __init__(self, game_state):
        """
        :param data: board, current player, move - score, move, calculated moves score
        :param parent: node
        :param childes: list of nodes
        """
        self.code = game_state.compress_instance()
        self.score = game_state.score  # the current move score

        self.childes = []
        self.calculated_score = 0
        self.parents = []
        self.visited = False

    def add_child(self, game_state=None, move=None, rate=0, is_win_move=False, dict_of_nodes=None):
        if isinstance(game_state, Node):
            child = game_state
        else:
            child = Node(game_state)

        child.parents.append(self)
        self.childes.append([child, move, rate, is_win_move])
        return child

    def add_child2(self, game_state=None, move=None, rate=0, is_win_move=False, dict_of_nodes={}):
        if isinstance(game_state, Node):
            child = game_state
        else:
            child = Node(game_state)

        if dict_of_nodes.get(child.code, None) is not None:
            child = dict_of_nodes[child.code]

        child.parents.append(self)
        self.childes.append([child, move, rate, is_win_move])

        return child

    def add_parent(self, parent):
        """
        will be more relevant for a graph with multiple parents
        """
        self.parents.append(parent)

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

    @staticmethod
    def find_best_move_rec(node, start_depth, current_depth, avg_n=3, player=True):

        if len(node.childes) == 0:
            return node.score[player] - node.score[not player]

        if start_depth - current_depth % 2 == 0:
            max_score = -10 ** 6
            for child in node.childes:
                tmp_score = Node.find_best_move_rec(child[0], start_depth, current_depth + 1)
                if tmp_score > max_score:
                    max_score = tmp_score
            return max_score

        else:
            scores = []
            for child in node.childes:
                scores.append(Node.find_best_move_rec(child[0], start_depth, current_depth + 1))
            scores.sort()
            return sum(scores[-avg_n:]) / avg_n

    def find_best_move(self):
        """
        run DFS until reach to bottom
        on the way up choose the score base on:
            if current player - best score
            if opponent - avg of top 3
        """
        max_score = -10 ** 6
        max_move = []
        for child in self.childes:
            tmp_score = Node.find_best_move_rec(child[0], 0, 1)
            if tmp_score > max_score:
                max_score = tmp_score
                max_move = [child[1]]  # [1] give the move to this node
            elif tmp_score == max_score:
                max_move.append(child[1])

        return random.choice(max_move)

    def expand_graph_not_from_leaf(self, steps):
        if len(self.childes) == 0:
            self.expand_tree(steps)

        for child in self.childes:
            if not child[0].visited:
                child[0].visited = True
                child[0].expand_graph_not_from_leaf(steps)

    def count_reachable_nodes(self, compare=True):
        self.visited = compare
        if len(self.childes) == 0:
            return 1

        counter = 1
        for child in self.childes:
            if child[0].visited != compare:
                counter += child[0].count_reachable_nodes(compare)
        return counter

    def count_reachable_nodes_tree(self, dict_nodes={}):
        dict_nodes[self.code] = self
        counter = 1
        for child in self.childes:
            counter += child[0].count_reachable_nodes_tree(compare)
        return counter

    def expand_tree(self, steps, game_state):
        """
        run only on the first step options and call in each step to expand_tree_rec()
        :return: recomanded step for best resulte
        """
        if steps <= 0:
            return

        if game_state.win[0] or game_state.win[1]:
            raise Exception

        game_state.get_all_moves_and_ranks()
        copy_instance = game_state.generate_copy()

        for position in copy_instance.all_possible_moves:
            for move in copy_instance.all_possible_moves[position]:
                game_state.set_last_click(position)
                res = game_state.do_move(move)

                if res is not None:
                    self.add_child(game_state, (position, move), game_state.last_move_rank, is_win_move=True)

                else:
                    child = self.add_child(game_state, (position, move), game_state.last_move_rank, is_win_move=False)
                    child.expand_tree(steps - 1, game_state)

                game_state.restore_instance_from_pre_instance(copy_instance)

    def expand_tree2(self, steps, game_state, dict_of_nodes={}):
        """
        run only on the first step options and call in each step to expand_tree_rec()
        :return: recomanded step for best resulte
        """

        dict_of_nodes[self.code] = self
        if steps <= 0:
            return

        if game_state.win[0] or game_state.win[1]:
            raise Exception

        game_state.get_all_moves_and_ranks()
        copy_instance = game_state.generate_copy()

        if len(self.childes) > 0:
            for child in self.childes:
                child[0].expand_tree2(steps - 1, game_state)

        else:
            for position in copy_instance.all_possible_moves:
                for move in copy_instance.all_possible_moves[position]:
                    game_state.set_last_click(position)
                    res = game_state.do_move(move)

                    if res is not None:
                        child = self.add_child2(game_state, (position, move), game_state.last_move_rank, True, dict_of_nodes)
                        dict_of_nodes[child.code] = child


                    else:
                        child = self.add_child2(game_state, (position, move), game_state.last_move_rank, False, dict_of_nodes)
                        child.expand_tree2(steps - 1, game_state)

                    game_state.restore_instance_from_pre_instance(copy_instance)

        return dict_of_nodes

    @staticmethod
    def switch_to_deeper_node(node1, node2):
        """
        replace in the the parents node with the less deep child to point to the deeper child
        """
        child1 = node1
        child2 = node2
        while len(child1.childes) > 0 and len(child2.childes) > 0:
            child1 = child1.childes[0][0]
            child2 = child2.childes[0][0]

        if len(child2.childes) > 0:
            for p in node1.parents:
                for i in range(len(p.childes)):
                    if p.childes[i][1] == node1:
                        p.childes[i][0] = node2
                        break
            return node2
        else:
            for p in node2.parents:
                for i in range(len(p.childes)):
                    if p.childes[i][1] == node2:
                        p.childes[i][0] = node1
                        break
            return node1
        print("end of function switch")

    def marge_nodes(self, node2):
        """
        self will be the node that we encounter for the first time and node2 is from the dict
        so the sub graph on self and his children is a tree -> no cycles
        then we add self parent to node2
        and keep the check on the children of self in case they have deeper child then dict

        if node2 has more childes then add them to self
        elif they have the same
            run this def on each of the kids
        else return
        """
        if len(self.childes) < len(node2.childes):
            self.childes = node2.childes

            for c in node2.childes:
                c[0].add_parent(self)
        elif len(self.childes) == len(node2.childes):

            for i in range(len(self.childes)):
                if self.childes[i][1] != node2.childes[i][1]:
                    raise Exception
                self.childes[i][0].marge_nodes(node2.childes[i][0])

    def is_all_childs_in_dict(self, dict):
        """
        self need to lead to a tree other wise we might get infinit loop
        :param dict:
        :return:
        """
        if dict.get(self.code, None) is None:
            return False
        for c in self.childes:
            if not c[0].is_all_childs_in_dict(dict):
                return False
        return True

    def delete_copies_rec(self, dict_of_nodes={}):
        dict_of_nodes[self.code] = self

        for i in range(len(self.childes)):
            if dict_of_nodes.get(self.childes[i][0].code, None) is None:
                self.childes[i][0].delete_copies_rec(dict_of_nodes)
            else:
                """
                self will be the node that we encounter for the first time and node2 is from the dict 
                so the sub graph on self and his children is a tree -> no cycles 
                then we add self parent to node2
                and keep the check on the children of self in case they have deeper child then dict
                """
                if not self.childes[i][0].is_all_childs_in_dict(dict_of_nodes):
                    dict_of_nodes[self.childes[i][0].code].add_parent(self)
                    self.childes[i][0].delete_copies_rec(dict_of_nodes)
                else:
                    dict_of_nodes[self.childes[i][0].code].add_parent(self)

        return dict_of_nodes

    def delete_copies(self, dict_of_nodes={}):
        for key in dict_of_nodes:
            dict_of_nodes[key].visited = self.visited
        return self.delete_copies_rec(dict_of_nodes)

    """    
    def __str__(self):
        return str(self.score)

    def __repr__(self):
        return "num of childs: " + str(len(self.childes))
    """

    def visit_all(self, visited=False):
        return
        self.visited = visited

        for child in self.childes:
            child[0].visit_all(visited)

def test1(steps):
    gs = ChessEngine.GameState()
    root = Node(gs)
    root.expand_tree(steps, gs)
    print("tree: ", root.count_reachable_nodes_tree)
    print("visit: ", root.count_reachable_nodes(not root.visited))
    # while True:
    dict_of_nodes = root.delete_copies()
    print(root.count_reachable_nodes(not root.visited))
    print(len(dict_of_nodes))
    print()
    return dict_of_nodes
    """
    4 steps: 
    count before delete: 207065
    count after delete:  71749
    dict length:         71749
    
    """


def test2(steps):
    gs2 = ChessEngine.GameState()
    root2 = Node(gs2)
    dict_of_nodes = root2.expand_tree2(steps, gs2)
    print(len(dict_of_nodes))

    print(root2.count_reachable_nodes(not root2.visited))
    dict_of_nodes = root2.delete_copies()
    print(root2.count_reachable_nodes(not root2.visited))
    print(len(dict_of_nodes))
    print()
    return dict_of_nodes
    """
    4 steps: 
    count before delete: 77849
    dict length:         77849
    count after delete:  1
    dict length:         71749
    
    3 steps:
    9323
    5783
    5783
    """


def compare(dict1, dict2):
    print("dict1: ", len(dict1))
    print("dict2: ", len(dict2))
    codes = []
    for key in dict1:
        if dict2.get(key, None) is None:
            print(key)
            codes.append(key)

    print("aaa")

    for key in dict2:
        if dict1.get(key, None) is None:
            print(key)
            codes.append(key)

    gs = []
    for c in codes:
        gs.append(ChessEngine.GameState(code=c))


if __name__ == '__main__':

    steps = 4
    dict1 = test1(steps)
    dict2 = test2(steps)
    # compare(dict1, dict2)

    print("A")
