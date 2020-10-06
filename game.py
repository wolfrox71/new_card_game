from random import shuffle
class player:
    def __init__(self):
        self.cards = []
        self.number_of_cards = 0
        self.ending_cards = []

class game:
    def __init__(self):
        self.number_of_cards = 30
        self.colours = ["red","green","blue"]
        self.number_of_players = 2
        self.players = []
        self.final_cards= [
            [],
            []
        ]
        self.deal()
        self.output_vals = self.winner()
        self.final_cards_per_player = [self.players[0].number_of_cards,self.players[1].number_of_cards]

    def deal(self):
        self.cards = []
        for x in self.colours:
            for i in range(1,self.number_of_cards+1):
                self.cards.append(f"{x},{i}")
        shuffle(self.cards)
        if len(self.players) == 0:
            self.cards_per_player = self.number_of_cards*len(self.colours)//self.number_of_players
            for j in range(self.number_of_players):
                self.players.append(player())
                for i in range(self.cards_per_player):
                    self.players[-1].cards.append(self.cards.pop(0))
                    

    def winner(self):
        output = []
        for x in range(self.cards_per_player):
            p1_card = self.players[0].cards.pop(0).split(",")
            p2_card = self.players[1].cards.pop(0).split(",")
            p1_colour = p1_card[0]
            p1_number = p1_card[1]
            p2_colour = p2_card[0]
            p2_number = p2_card[1]
            
            if p1_colour == p2_colour:
                if int(p1_number) > int(p2_number):
                    winner = "Player 1"
                    self.final_cards[0].append(p1_card)
                    self.final_cards[0].append(p2_card)
                    self.players[0].number_of_cards += 1

                else:
                    winner = "Player 2"
                    self.players[1].number_of_cards += 1
                    self.final_cards[1].append(p1_card)
                    self.final_cards[1].append(p2_card)

            elif self.colours[self.colours.index(p1_colour)-1] == p2_colour:
                winner = "Player 1"
                self.players[0].number_of_cards += 1
                self.final_cards[0].append(p1_card)
                self.final_cards[0].append(p2_card)

            else:
                winner = "Player 2"
                self.players[1].number_of_cards += 1
                self.final_cards[1].append(p1_card)
                self.final_cards[1].append(p2_card)
            output.append([p1_card, p2_card ,winner])
        return output