import time
import asteriskHelper
import asyncio
import socket
import random

roles = ["wolves", "seear", "villager", "witch"]
class Player:
    def __init__(self, roleNumber, playerNuber):
        self.role = roles[roleNumber]
        self.number = playerNuber
        self.isAlive = True
        self.clientObject = None

players = []
def getRoleCount(roleName):
    counter = 0
    for player in players:
        if  player.role == roleName:
            counter += 1
    return counter

#find all players with a specific role
def getListOfAllAlivePlayersWithRole(roleName):
    playerOfRole = []
    for player in players:
        if (player.role == roleName and player.isAlive):
            playerOfRole.append(player)
    return playerOfRole

def isGameOver():
    return len(getListOfAllAlivePlayersWithRole(players)) <= 1 or getRoleCount("wolves") <= 0 or getRoleCount("wolves") >= len(getAllPlayersAlive(players)) - getRoleCount("wolves")

async def requestUserInput(playerNumber):
    lastUserInput = asteriskHelper.getUserInput(playerNumber)
    while (lastUserInput == playerNumber or lastUserInput.isdigit() == False):
        asteriskHelper.playAudio("You can not pick yourself")
        lastUserInput = asteriskHelper.getUserInput(playerNumber)
    return lastUserInput

async def requestMulitibleUserInputs(listOfPlayers):
    getUserInputs = []
    for player in listOfPlayers:
        getUserInputs.append(requestUserInput(player))
    results = await asyncio.gather(*getUserInputs)
    return results

#note that it go on even if there is a draw
def getMostVoteResult(results):
    max(set(results), key=results.count)

def getAllPlayersAlive():
    return [player for player in players if player.isAlive == True]

def reassignRoles():
    rolePool = []
    if len(players) < 4:
        print("Not enough players to start the game")
        return
    if len(players) == 5:
        rolePool = ["wolves", "seear", "witch", "villager", "villager"]
    if len(players) == 6:
        rolePool = ["wolves", "wolves", "seear", "witch", "villager", "villager"]
    if len(players) == 7:
        rolePool = ["wolves", "wolves", "seear", "witch", "villager", "villager", "villager"]
    if len(players) == 8:
        rolePool = ["wolves", "wolves", "seear", "witch", "villager", "villager", "villager", "villager"]
    if len(players) == 9:
        rolePool = ["wolves", "wolves", "seear", "witch", "villager", "villager", "villager", "villager", "villager"]
    else:
        print("Not yet implemented for more than 9 players")

    for player in players:
        assignedRole = rolePool.pop(random.randint(0, len(rolePool)-1))
        player.role = assignedRole

HOST = "localhost"  # Standard loopback interface address (localhost)
PORT = 28830  # Port to listen on (non-privileged ports are > 1023)

numberOfPlayers = int(input("Enter number of players: "))
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    for i in range(numberOfPlayers):
        conn, addr = s.accept()
        print(f"Connected by {addr}")
        players.append(Player(i % len(roles), i+1))
        players[-1].clientObject = conn
        players[-1].clientObject.sendall(f"Your player number is {i+1}".encode())
print(f"The game can start now")
#add all of the players here and wait for them to game to start
reassignRoles()

#start game
    #introduce each player by giving him access to the 
#for player in players:
    #asteriskHelper.givePlayersRightToSpeak([player])
    #time.sleep(5000) #give them some time to introduce
    
#first round (makes not difference for the current roles, so just ignore it)


#start the normal game loop
while(isGameOver() == True):
    #night time
    asteriskHelper.playAudio("Everyone is falling a sleep", players)
    asteriskHelper.playAudio("The seears are waking up", players)
    
    allSeears = getListOfAllAlivePlayersWithRole("seears")
    for seear in allSeears:
        asteriskHelper.playAudio(f"Seear please choose someone to see", players)
        result = asyncio.run(requestUserInput(seear.playerNumber))
        for player in players:
            if player.number == result:
                if(player.role == "wolves"):
                    asteriskHelper.playAudio("The person is a wolve", players)
                else:
                    asteriskHelper.playAudio("The person is not a wolve", players)
    


    allWolves = getListOfAllAlivePlayersWithRole("wolves")
    asteriskHelper.connectPlayersPrivatly(allWolves)
    asteriskHelper.playAudio("Introduction to wolves voting system", players) #maybe we can even tell them even the number of the victim
    wolvesVotingResult = asyncio.run(requestMulitibleUserInputs(allWolves))
    possibleVictim = getMostVoteResult(wolvesVotingResult)
    

    allWitches = getListOfAllAlivePlayersWithRole("witch")
    asteriskHelper.connectPlayersPrivatly(allWitches)
    asteriskHelper.playAudio("Introduction to witches voting system", players) #maybe we can even tell them even the number of the victim 
    witchesVotingResult = asyncio.run(requestMulitibleUserInputs(allWitches))
    if(getMostVoteResult(witchesVotingResult) == 1):
        #now it's time to kill someone
        asteriskHelper.playAudio("Introduce who to kill", players)
        seearsKillResult = requestMulitibleUserInputs(allWitches)
        for player in players:
            if player.playerNumber == getMostVoteResult(seearsKillResult):
                player.isAlive = False
                break
    elif(getMostVoteResult(witchesVotingResult) == 2):
        #heal the possible victim
        possibleVictim = -1
    
    #daytime
    asteriskHelper.connectPlayersPrivatly(players)
    if(possibleVictim == -1):
        asteriskHelper.playAudio("no one died", players)
    else:
        for player in players:
            if(player.number == possibleVictim):
                player.isAlive == False
        asteriskHelper.playAudio("someone passed away", players) # also maybe tell the number
    asteriskHelper.givePlayersRightToSpeak(getAllPlayersAlive())

    #village voting system 
    asteriskHelper.playAudio("Ask if they want to kill someone", players) #maybe we can even tell them even the number of the victim 
    villageVotingResult = asyncio.run(requestMulitibleUserInputs(getAllPlayersAlive()))
    if(getMostVoteResult(villageVotingResult) == 1):
        #they decided to 
        asteriskHelper.playAudio("Introduce who to kill", players)
        villageKillResult = requestMulitibleUserInputs(getAllPlayersAlive())
        for player in players:
            if player.playerNumber == getMostVoteResult(villageKillResult):
                player.isAlive = False
                break

#game over
for player in players:
    asteriskHelper.kickPlayer(player.number)

#finished

#TODO:
#mute dead players
#figure out if we can play audio from an ai to call each player by his number