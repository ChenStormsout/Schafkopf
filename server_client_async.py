from env import NaivPlayer,SchafkopfEnv
import asyncio


class Server:
    def __init__(self) -> None:
        self.players = []
        self.current_player = 0
        self.env=SchafkopfEnv()

    def register_player(self, player):
        self.players.append(player)

    async def step(self, player,action):
        while self.players[self.current_player] != player:
            print(player)
            asyncio.sleep(0.01)
        # action = None
        # while not type(action) == int:
        #     action = input(f"What action shall player {self.current_player} do?\n")
        #     try:
        #         action = int(action)
        #     except:
        #         pass
        print(f"Player {self.current_player} did a {action}.")
        return_values=self.env.step(action)
        if return_values[2]:
            print("Game has ended. New Game starting.\n\n")
            self.schafkopf_env.reset()
        self.current_player = self.env.players_turn
        # if self.current_player >= len(self.players):
        #     self.current_player = 0


class Client:
    def __init__(self, server) -> None:
        self.server = server
        self.server.register_player(self)
        self.logic=NaivPlayer(self.server.env)

    async def step(self):
        for i in range(10):
            await asyncio.gather(self.server.step(self,self.logic.step()))


server = Server()
players = []

for i in range(4):
    players.append(Client(server))


async def main():
    await asyncio.gather(
        players[0].step(), players[1].step(), players[2].step(), players[3].step()
    )


asyncio.run(main())
