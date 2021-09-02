import unittest
from io import StringIO
from unittest.mock import patch

import os
import ChessEngine as ChessEngine
# import ChessEngine

game_state = ChessEngine.GameState()
game_state.to_print = True
game_state.get_all_moves_and_ranks()


def load(file_name):
    text = open("tests/"+file_name, "r")
    text = text.read().split(";")[:-1]

    tmp_text = []
    block = []
    for t in text:
        block.append(t[1:])
        if len(t) > 12: # click print length is 11, +1 for error margin
            tmp_text.append(block)
            block = []

    if "Won" in t:
        tmp_text[-1][-1] = tmp_text[-1][-1] + ";" + t
    return tmp_text


def click():
    for ci in input[0][:-1]:
        ci_tuple = eval(ci)
        game_state.handle_mouse_click(ci_tuple)


class MyTestCase(unittest.TestCase):
    def runTest(self, given_answer, expected_out):
        with patch('builtins.input', return_value=given_answer), patch('sys.stdout', new=StringIO()) as fake_out:
            click()
            self.assertEqual(fake_out.getvalue().strip(), expected_out)


    def test(self):
        global game_state
        global input

        path = os.getcwd() + "/tests"
        files = os.listdir(path)

        for f in files:
            game_state = ChessEngine.GameState()
            game_state.get_all_moves_and_ranks()
            input = load(f)

            while len(input) > 0:
                self.runTest("", ';\n'.join(input[0])+";")
                input.pop(0)


if __name__ == '__main__':
    unittest.main()
