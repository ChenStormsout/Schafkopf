from threading import Thread
from queue import Queue
import time
from env import NaivPlayer, SchafkopfEnv


class Server(Thread):
    def __init__(self) -> None:
        Thread.__init__(self)
        self.players_queues = []
        self.current_player = 0
        self.action_queue = Queue()
        self.global_counter = 0
        self.env=SchafkopfEnv()

    def register_player(self, player):
        self.players_queues.append(player.state_queue)
        player.action_queue = self.action_queue
        player.logic=player.logic_func(self.env)

    def run(self):
        self.env.reset()
        while True:
            current_queue = self.players_queues[self.current_player]
            observation = (3, 1, False, dict())
            current_queue.put(observation)
            got_action = False
            while not got_action:
                if not self.action_queue.empty():
                    action = self.action_queue.get()
                    print(f"Player {self.current_player} did action  {action}")
                    return_values=self.env.step(action)
                    if return_values[2]==True:
                        self.env.reset()
                    got_action = True
                    self.current_player +=1
                    if self.current_player >=3:
                        self.current_player = 0
                else:
                    time.sleep(0.1)


class Client(Thread):
    def __init__(self, server) -> None:
        Thread.__init__(self)
        self.server = server
        self.state_queue = Queue()
        self.action_queue = None
        self.logic_func=NaivPlayer
        self.logic=None
        self.server.register_player(self)

    def run(self):
        while True:
            if not self.state_queue.empty():
                state=self.state_queue.get()
                move=self.logic.step()
                self.action_queue.put(move)
            else:
                time.sleep(1)


server = Server()
players = []

for i in range(4):
    players.append(Client(server))


def main():
    for player in players:
        server.register_player(player)
        player.start()
    server.start()


main()
