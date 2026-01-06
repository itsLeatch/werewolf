"""Shared data models to avoid circular imports"""

roles = ["wolves", "seer", "villager", "witch"]

class Player:
    def __init__(self, roleNumber, playerNumber):
        self.role = roles[roleNumber]
        self.number = playerNumber
        self.isAlive = True
        self.gamePlayerNum = -1  # To be assigned when game starts

players = []

def createPlayer(playerNumber):
    """Create a new player and add to the players list"""
    user = Player(0, playerNumber)
    players.append(user)
    return user

def removePlayer(playerNumber):
    """Remove a player from the global players list by channel/number"""
    global players
    players = [p for p in players if p.number != playerNumber]

def getAllPlayersAlive():
    return [player for player in players if player.isAlive == True]

def getRoleCount(roleName):
    counter = 0
    for player in players:
        if player.role == roleName:
            counter += 1
    return counter

def getListOfAllAlivePlayersWithRole(roleName):
    playerOfRole = []
    for player in players:
        if (player.role == roleName and player.isAlive):
            playerOfRole.append(player)
    return playerOfRole

def assignGamePlayerNumbers():
    alivePlayers = getAllPlayersAlive()
    for index, player in enumerate(alivePlayers):
        player.gamePlayerNum = index + 1

def isGameOver():
    return len(getAllPlayersAlive()) <= 1 or getRoleCount("wolves") <= 0 or getRoleCount("wolves") >= len(getAllPlayersAlive()) - getRoleCount("wolves")
