from abc import abstractclassmethod
import numpy as np
import gymnasium as gym
from gymnasium import spaces

# Grundtarif = 5; Solotarif = 20
# Sie = vierfacher Solotarif,
# Tout = doppelter Solotarif,
# Farb-Solo = 20,
# Wenz = 20,
# Geier = 20,
# Sauspiel = 5,
# Ramsch = 5

# 4x Sauspiel + 1*Ramsch + 1*Sie + 2*4*Farb-Solo, 2*4*Wenz, 2*4*Geier = 30 Spielmodus

# Ass =11
# 10 = 10
# König = 4
# Ober = 3
# Unter 2
# 9 = 0
point_dict = {"Ass": 11, "10": 10, "König": 4, "Ober": 3, "Unter": 2, "9": 0}
card_type_hierarchy_dict = {
    "Ober": 6,
    "Unter": 5,
    "Ass": 4,
    "10": 3,
    "König": 2,
    "9": 1,
}
card_symbol_hierarchy_dict = {"Eichel": 4, "Blatt": 3, "Herz": 2, "Schelln": 1}
gamemode_dict = {"Solo": 4, "Wenz": 3, "Geier": 2, "Sauspiel": 1, "Ramsch": 0}
# Ober, Unter, Ass, 10, König, 9
# Eichel, Blatt, Herz, Schelln

# Vier Farben u. je sechs karten => 24 Karten
# Observation aus Spielerposition (4), Karten auf der Hand (24)*Anzahl der Karten, Karten auf dem Stapel(24), Encoding für den Spielmodus (30), und Ansagerpostion (4)

# def decode_cards(card_index):
#     color_index=card_index%4
#     if color_index==0:
#         color= "Eichel"
#     elif color_index==1:
#         color= "Blatt"
#     elif color_index==2:
#         color= "Herz"
#     elif color_index==3:
#         color= "Schellen"
#     card_type_index=card_index//4
#     if card_type_index==0:
#         card_type= "Ass"
#     elif card_type_index==1:
#         card_type= "Ass"
#     elif card_type_index==2:
#         card_type= "10"
#     elif card_type_index==3:
#         card_type= "König"
#     elif card_type_index==4:
#         card_type= "Ober"
#     elif card_type_index==5:
#         card_type= "Unter"
#     elif card_type_index==6:
#         card_type= "9"
#     return " ".join([color, card_type])


class Card:
    def __init__(self, symbol, card_type, card_number) -> None:
        self.symbol = symbol
        self.card_type = card_type
        self.card_number = card_number


class CardStack:
    def __init__(self) -> None:
        self.card_counter = 0
        self.card_dict = dict()
        self.player_card_order_dict = dict()
        for i in range(4):
            self.card_dict[i] = None
            self.player_card_order_dict[i] = None

    def put_card(self, card, player_position):
        self.card_dict[self.card_counter] = card
        self.player_card_order_dict[self.card_counter] = player_position
        self.card_counter += 1
        if self.card_counter > 3:
            return True
        return False

    def reset(self):
        self.card_counter = 0
        for i in range(4):
            self.card_dict[i] = None
            self.player_card_order_dict[i] = None

    def show_cards(self):
        return [
            [card.card_type, card.symbol, card.card_number]
            if isinstance(card, Card)
            else [-1, -1, -1]
            for card in self.card_dict.values()
        ]


class Player:
    def __init__(self, player_position) -> None:
        self.cards = [None for _ in range(6)]
        self.position = player_position
        self.won_cards = []
        self.points = 0

    def give_cards(self, player_cards):
        self.cards = player_cards

    def show_cards(self):
        return [
            [card.card_type, card.symbol, card.card_number]
            if isinstance(card, Card)
            else [-1, -1, -1]
            for card in self.cards
        ]

    def cards_left(self):
        return sum([1 if card is not None else 0 for card in self.cards])

    def put_card(self, card_stack, card_index):
        if self.cards[card_index] is None:
            return False, False
        stack_full = card_stack.put_card(self.cards[card_index], self.position)
        self.cards[card_index] = None
        return True, stack_full

    # def change_player_position(self):
    #     self.position += 1
    #     if self.position > 3:
    #         self.position = 0


def generate_card_deck(rng):
    cards = []
    card_symbols = ["Ass", "10", "König", "Unter", "Ober", "9"]
    card_colors = ["Eichel", "Blatt", "Herz", "Schelln"]
    card_number = 0
    for card_symbol in card_symbols:
        for card_color in card_colors:
            cards.append(Card(card_color, card_symbol, card_number))
            card_number += 1
    rng.shuffle(cards)
    return cards


def hot_encode(card_number, len=24):
    return [1 if i == card_number else 0 for i in range(0, len)]


class GameMode:
    @abstractclassmethod
    def __init__(self) -> None:
        pass

    @abstractclassmethod
    def check_if_valid_move(self, player, move, stack):
        pass

    @abstractclassmethod
    def assign_points(self, card_stack, players):
        pass

    @abstractclassmethod
    def determine_winner(self, players):
        pass


class Sauspiel(GameMode):
    def __init__(self, card_sympbol):
        super(Sauspiel, self).__init__()
        self.name = "Sauspiel"
        self.card_symbol = card_sympbol
        self.calling_players = []
        self.countering_players = []

    def define_teams(self, players, calling_player_idx):
        calling_player = players[calling_player_idx]
        for player in players.values():
            for card in player.cards:
                if card.symbol == self.card_symbol and card.card_type == "Ass":
                    partner_player = player
        if partner_player == calling_player:
            return False
        self.calling_players = [partner_player, calling_player]
        self.countering_players = [
            player for player in players.values() if not player in self.calling_players
        ]
        return True

    def determine_winner(self):
        points_calling_players = sum([player.points for player in self.calling_players])
        points_countering_players = sum(
            [player.points for player in self.countering_players]
        )
        if points_calling_players > points_countering_players:
            print(
                f"The winners are: {', '.join(['Player ' + str(player.position) for player in self.calling_players])} with {points_calling_players} to {points_countering_players}"
            )
            return self.calling_players
        print(
            f"The winners are: {', '.join(['Player ' + str(player.position) for player in self.countering_players])} with {points_countering_players} to {points_calling_players}"
        )
        return self.countering_players

    def check_if_valid_move(self, player, move, stack):
        if stack.card_dict[0] is not None:
            stack_color = self.check_color(stack.card_dict[0])
            card_color = self.check_color(player.cards[move])
            if not self.check_called_sau(stack,player.cards[move],player):
                return False
            if stack_color == card_color:
                return True
            if (
                sum(
                    [
                        stack_color == self.check_color(card)
                        for card in player.cards
                        if card is not None
                    ]
                )
                == 0
            ):
                return True
            return False
        return True

    def assign_points(self, card_stack, players):
        print("Evaluating points of a full stack")
        print("The stack has the following cards: ", card_stack.show_cards())
        card_hierachy = [
            self.check_for_right_color(card_stack.card_dict[0], card)
            for card in card_stack.card_dict.values()
        ]
        max_hierachy = max(card_hierachy)
        is_high_card = [hierarchy == max_hierachy for hierarchy in card_hierachy]
        highest_cards = []
        for idx in range(0, 4):
            if is_high_card[idx]:
                highest_cards.append(card_stack.card_dict[idx])
        cards_type_value = [
            card_type_hierarchy_dict[card.card_type] for card in highest_cards
        ]
        max_cards_type_value = max(cards_type_value)
        if len(highest_cards) > 1:
            print("If statement")
            highest_cards = [
                highest_cards[idx]
                for idx in range(len(highest_cards))
                if cards_type_value[idx] == max_cards_type_value
            ]
            if len(highest_cards) > 1:
                cards_symbol_value = [
                    card_symbol_hierarchy_dict[card.symbol]
                    for card in highest_cards
                ]
                max_cards_symbol_value = max(cards_symbol_value)
                highest_cards = [
                    highest_cards[idx]
                    for idx in range(len(highest_cards))
                    if cards_symbol_value[idx] == max_cards_symbol_value
                ]
        highest_card_position = np.argmax(
            [highest_cards[0] == card for card in card_stack.card_dict.values()]
        )
        player_who_gets_stack = card_stack.player_card_order_dict[highest_card_position]
        print(f"Player {player_who_gets_stack} gets the stack.")
        for card in card_stack.card_dict.values():
            players[player_who_gets_stack].points += point_dict[card.card_type]
        card_stack.reset()
        return player_who_gets_stack

    def check_color(self, card):
        if (
            card.symbol == "Herz"
            or card.card_type == "Ober"
            or card.card_type == "Unter"
        ):
            return "Trumpf"
        else:
            return card.symbol

    def check_for_right_color(self, first_card, relevant_card):
        if self.check_color(first_card) == self.check_color(relevant_card):
            return 1
        if (
            self.check_color(first_card) != "Trumpf"
            and self.check_color(relevant_card) == "Trumpf"
        ):
            return 2
        return 0

    def check_called_sau(self, stack, card,player):
        if self.check_color(card) == self.check_color(stack.card_dict[0]) and self.card_symbol == stack.card_dict[0].symbol and self.card_symbol==card.symbol:
            if max([player_card.card_type=="Ass" and player_card.symbol == self.card_symbol for player_card in player.cards if not player_card is None])!=0:
                if card.card_type != "Ass" or card.symbol != self.card_symbol:
                    return False    
        return True


class SchafkopfEnv(gym.Env):
    """Custom Environment that follows gym interface"""

    def __init__(self, random_seed=42):
        super(SchafkopfEnv, self).__init__()
        self.game_modes = [
            Sauspiel("Eichel"),
            Sauspiel("Blatt"),
            Sauspiel("Herz"),
            Sauspiel("Schelln"),
        ]
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(6 * 24 + len(self.game_modes),), dtype=np.uint8
        )
        self.action_space = spaces.Discrete(6)
        self.next_random_seed = random_seed
        self.players = dict()
        self.players_turn = 0
        self.leading_players = []
        for i in range(0, 4):
            player = Player(i)
            self.players[i] = player
        self.card_stack = CardStack()
        self.players_turn_to_start = 0
        self.game_mode_offers = dict()

    def reset(self):
        self.rng = np.random.default_rng(seed=self.next_random_seed)
        self.next_random_seed = self.rng.integers(0, high=np.iinfo(np.int16).max)
        self.game_mode_offers = dict()
        card_deck = generate_card_deck(self.rng)
        for i in range(0, 4):
            self.players[i].give_cards(
                card_deck[i * 3 : i * 3 + 3] + card_deck[(i + 4) * 3 : (i + 4) * 3 + 3]
            )
        self.set_game_mode(None, self.players_turn_to_start)
        for player in self.players.values():
            player.points = 0
        for player_idx in self.players.keys():
            print(
                f"Player {self.players[player_idx].position} has:",
                self.players[player_idx].show_cards(),
            )
        self.players_turn = (
            self.players_turn_to_start
        )  # Remove later once game mode is selected more sophisticated
        self.players_turn_to_start += 1
        if self.players_turn_to_start > 3:
            self.players_turn_to_start = 0
        print(f"Player {self.players_turn} is starting.")
        return self.get_state()

    def set_game_mode(self, game_mode_idx, calling_player):
        if game_mode_idx is None:
            self.current_game_mode = None
        else:
            self.current_game_mode = self.game_modes[game_mode_idx]
            self.current_game_mode.define_teams(self.players, calling_player)
        self.game_mode_idx = game_mode_idx
        

    def get_state(self):
        state = []
        state += self.players[self.players_turn].show_cards()
        # print(
        #     f"Player {self.players[self.players_turn].position} has :",
        #     self.players[self.players_turn].show_cards(),
        # )
        state += self.card_stack.show_cards()
        state = (
            [hot_encode(s[2]) for s in state]
            + [hot_encode(self.game_mode_idx, len(self.game_modes))]
            + [hot_encode(self.players_turn, len(self.players))]
        )
        return state

    def step(self, action):
        if self.current_game_mode is None:
            if action != 0:
                offer=self.game_modes[action - 1]
                if not offer in self.game_mode_offers.values():
                    self.game_mode_offers[self.players_turn] = offer
                else:
                    self.game_mode_offers[self.players_turn] = None
            else:
                self.game_mode_offers[self.players_turn] = None
            self.players_turn += 1
            if self.players_turn > 3:
                self.players_turn = 0
            if len(self.game_mode_offers)==4:
                game_mode_rankings = [gamemode_dict[game_mode.name] if not game_mode is None else -1 for game_mode in self.game_mode_offers.values()]
                max_ranking = max(game_mode_rankings)
                high_game_modes=[]
                for idx,game_mode in enumerate(self.game_mode_offers.values()):
                    if game_mode_rankings[idx]==max_ranking:
                        high_game_modes.append(game_mode)
                if len(high_game_modes)>1:
                    game_mode_rankings=[card_symbol_hierarchy_dict[mode.card_symbol] for mode in high_game_modes if not mode is None]
                    max_ranking = np.argmax(game_mode_rankings) #here
                    high_game_modes=[high_game_modes[max_ranking]]
                player_w_highest_offering=np.argmax([True if mode==high_game_modes[0] else False for mode in self.game_mode_offers.values()])
                game_mode_idx=np.argmax([[True if mode==high_game_modes[0] else False for mode in self.game_modes]])
                self.set_game_mode(game_mode_idx,player_w_highest_offering)
                print(f"The current game mode is: {self.current_game_mode.card_symbol} called by Player {player_w_highest_offering}")
            return self.get_state(), 0, False, dict()
        else:
            print(
                f"Player {self.players[self.players_turn].position} is trying to put the card {self.players[self.players_turn].cards[action].symbol +' '+self.players[self.players_turn].cards[action].card_type}."
            )
            if self.current_game_mode.check_if_valid_move(
                self.players[self.players_turn], action, self.card_stack
            ):
                valid_move, stack_full = self.players[self.players_turn].put_card(
                    self.card_stack, action
                )
            else:
                valid_move = False
            if valid_move:
                print("Valid move!")
            else:
                print("Invalid move!")
                raise ValueError("Player has chosen invalid move!")
            for player in self.players.values():
                print(f"Player {player.position} has", player.show_cards())
            observation = self.get_state()
            if not valid_move:
                return observation, -1, True, dict()
            self.players_turn += 1
            if self.players_turn > 3:
                self.players_turn = 0
            if stack_full:
                self.players_turn = self.current_game_mode.assign_points(
                    self.card_stack, self.players
                )
            reward = 1
            done = False
            if stack_full and self.players[self.players_turn].cards_left() == 0:
                done = True
                winners = self.current_game_mode.determine_winner()

            return observation, reward, done, dict()

class NaivPlayer:
    def __init__(self,schafkopf_env,random_seed=42) -> None:
        # self.player_number=player_number
        self.rng = np.random.default_rng(random_seed)
        self.schafkopf_env=schafkopf_env
        self.schafkopf_env.reset()

    def step(self):
        player_himself=self.schafkopf_env.players[self.schafkopf_env.players_turn]
        current_game_mode=self.schafkopf_env.current_game_mode
        stack=self.schafkopf_env.card_stack
        valid_options=[]
        if current_game_mode is None:
            valid_options=list(range(len(self.schafkopf_env.game_modes)))
        else:
            for idx, card in enumerate(player_himself.cards):
                if card is None:
                    continue
                if current_game_mode.check_if_valid_move(player_himself, idx, stack):
                    valid_options.append(idx)
        random_move=self.rng.choice(valid_options)
        return_values=self.schafkopf_env.step(random_move)
        if return_values[2]:
            print("Game has ended. New Game starting.\n\n")
            self.schafkopf_env.reset()

naivplayer=NaivPlayer(SchafkopfEnv())
for _ in range(400):
    naivplayer.step()

# env = SchafkopfEnv()
# obs = env.reset()
# step_values = env.step(3)
# step_values = env.step(0)
# step_values = env.step(0)
# step_values = env.step(0)
# print("Finished to select game mode!")
# # print(obs)
# # for ob in obs:
# #     print(ob)
# print("\n \n")
# for player in env.players.values():
#     print(player.show_cards())

# step_values = env.step(0)
# step_values = env.step(5)
# step_values = env.step(0)
# step_values = env.step(0)
# if step_values[1] == 1:
#     print("Sucessfully finished first round! \n \n")
# else:
#     print("Failed to finish first round \n \n")
# step_values = env.step(3)
# step_values = env.step(1)
# step_values = env.step(4)
# step_values = env.step(2)
# if step_values[1] == 1:
#     print("Sucessfully finished second round! \n \n")
# else:
#     print("Failed to finish second round \n \n")
# step_values = env.step(1)
# step_values = env.step(1)
# step_values = env.step(4)
# step_values = env.step(5)
# if step_values[1] == 1:
#     print("Sucessfully finished third round! \n \n")
# else:
#     print("Failed to finish third round \n \n")
# step_values = env.step(2)
# step_values = env.step(0)
# step_values = env.step(2)
# step_values = env.step(3)
# if step_values[1] == 1:
#     print("Sucessfully finished fourth round! \n \n")
# else:
#     print("Failed to finish fourth round \n \n")
# step_values = env.step(5)
# step_values = env.step(4)
# step_values = env.step(1)
# step_values = env.step(2)
# if step_values[1] == 1:
#     print("Sucessfully finished fifth round! \n \n")
# else:
#     print("Failed to finish fifth round \n \n")
# step_values = env.step(3)
# step_values = env.step(3)
# step_values = env.step(5)
# step_values = env.step(4)
# if step_values[1] == 1:
#     print("Sucessfully finished sixth round! \n \n")
# else:
#     print("Failed to finish sixth round \n \n")

# print("Game 2")
# obs = env.reset()
# step_values = env.step(4)
# step_values = env.step(3)
# step_values = env.step(2)
# step_values = env.step(1)

# print("Finished to select game mode!")
# print("\n \n")
# for player in env.players.values():
#     print(player.show_cards())

# step_values = env.step(0)
# step_values = env.step(0)
# step_values = env.step(4)
# step_values = env.step(2)
# if step_values[1] == 1:
#     print("Sucessfully finished first round! \n \n")
# else:
#     print("Failed to finish first round \n \n")
# step_values = env.step(3)
# step_values = env.step(2)
# step_values = env.step(2)
# step_values = env.step(1)
# if step_values[1] == 1:
#     print("Sucessfully finished second round! \n \n")
# else:
#     print("Failed to finish second round \n \n")
# step_values = env.step(3)
# step_values = env.step(4)
# step_values = env.step(1)
# step_values = env.step(4)
# if step_values[1] == 1:
#     print("Sucessfully finished third round! \n \n")
# else:
#     print("Failed to finish third round \n \n")
# step_values = env.step(5)
# step_values = env.step(4)
# step_values = env.step(5)
# step_values = env.step(0)
# if step_values[1] == 1:
#     print("Sucessfully finished fourth round! \n \n")
# else:
#     print("Failed to finish fourth round \n \n")
# step_values = env.step(5)
# step_values = env.step(0)
# step_values = env.step(5)
# step_values = env.step(1)
# if step_values[1] == 1:
#     print("Sucessfully finished fifth round! \n \n")
# else:
#     print("Failed to finish fifth round \n \n")
# step_values = env.step(3)
# step_values = env.step(3)
# step_values = env.step(2)
# step_values = env.step(1)
# if step_values[1] == 1:
#     print("Sucessfully finished sixth round! \n \n")
# else:
#     print("Failed to finish sixth round \n \n")
