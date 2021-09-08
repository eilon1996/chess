import json
import requests
import pygame

class Firebase:

    FIREBASE_URL = "https://chess-e9528-default-rtdb.firebaseio.com/rooms"

    def __init__(self, room_id, is_host, host_color=None):

        self.room_id = room_id
        self.is_host = is_host
        if host_color is None:
            self.host_color = self.get_host_color()
        else:
            self.host_color = host_color
        self.last_move = ""

    def get_host_color(self):
        response = requests.get(Firebase.FIREBASE_URL + "/" + self.room_id + "/.json").text
        if response == 'null':
            raise Exception("return null")
        response = response.replace('null', 'None')
        dict = eval(response)
        return dict["host_color"]

    def join_room(self):
        room = {"guest_online": 1}
        room = json.dumps(room)
        requests.patch(Firebase.FIREBASE_URL + "/" + self.room_id + ".json", room)

    def get_my_color(self):
        response = requests.get(Firebase.FIREBASE_URL + "/" + self.room_id + "/.json").text
        if response == 'null':
            raise Exception("return null")
        response = response.replace('null', 'None')
        dict = eval(response)
        ans = not dict["host_color"] ^ self.is_host
        return ans

    def is_opponent_online(self):
        if self.is_host:
            online = "/guest_online"
        else:
            online = "/host_online"

        response = requests.get(Firebase.FIREBASE_URL + "/" + self.room_id + online + "/.json").text
        if response == 'null':
            raise Exception("return null")
        print(response)
        return response


    @staticmethod
    def is_room_exist(room_id):
        response = requests.get(Firebase.FIREBASE_URL + "/" +room_id+ "/.json").text
        if response == 'null':
            print("room not exist")
            return False
        print("room exist")
        return True

    def create_room(self):
        room = {self.room_id: {"host_color": self.host_color,
                              "host_online": 1,
                              "guest_online": 0,
                              "last_move": ""
                          }}
        room = json.dumps(room)
        res = requests.patch(Firebase.FIREBASE_URL + "/.json", room)
        if res.ok:
            print("room created")
        else:
            print(res)

    def delete_room(self):
        res = requests.delete(Firebase.FIREBASE_URL + "/" + self.room_id + "/.json")
        print(res)


    def set_last_move(self, move):
        move = str(move[0][0]) + str(move[0][1]) + str(move[1][0]) + str(move[1][1])
        self.last_move = move
        room = {"last_move": move}
        room = json.dumps(room)
        requests.patch(Firebase.FIREBASE_URL + "/" + self.room_id + ".json", room)

    def get_last_move(self):

        res = requests.get(Firebase.FIREBASE_URL + "/" + self.room_id + "/last_move" + "/.json")
        response = res.text[1:-1]
        if response == 'null':
            raise Exception("return null")
        response = response.replace('null', 'None')
        return response

    def wait_for_opponent_move(self):
        while True:
            last_move = self.get_last_move()
            if last_move != self.last_move:
                move = [(int(last_move[0]), int(last_move[1])), (int(last_move[2]), int(last_move[3]))]
                return move

    def wait_for_opponent_to_connect(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise Exception("goodbye")
            if self.is_opponent_online() == "1":
                return "1"

if __name__ == "__main__":

    f = Firebase("123", 1, host_color=1)
    f.delete_room()