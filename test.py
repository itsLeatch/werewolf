roles = ["wolves", "seear", "villager", "witch"]

class Player:
    def __init__(self, roleNumber, playerNuber):
        self.role = roles[roleNumber]
        self.number = playerNuber
        self.isAlive = True


def getAllPlayersAlive():
    return [player for player in players if player.isAlive == True]
players = [Player(0, 1), Player(1, 2), Player(2, 3), Player(3, 4), Player(0, 5), Player(2, 6)]
players[2].isAlive = False
players[3].isAlive = False
players[4].isAlive = False
print(len(getAllPlayersAlive()))
