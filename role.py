import time
import asteriskHelper
import asyncio

roles = ["wolves", "seear", "villager", "witch"]
class Player:
    def __init__(self, roleNumber, playerNuber):
        self.role = roles[roleNumber]
        self.number = playerNuber
        self.isAlive = True


players = []

def getRoleCount(roleName):
    counter = 0
    for player in players:
        if  player.role == roleName:
            counter += 1
    return counter

def getListOfAllPlayersWithRole(roleName):
    playerOfRole = []
    for player in players:
        if (player.role == roleName):
            playerOfRole.append(player)
    return playerOfRole


def isGameOver():
    return len(players) <= 1 or getRoleCount("wolves") <= 0 or getRoleCount("wolves") >= len(players) - getRoleCount("wolves")

async def requestUserInput(playerNumber):
    lastUserInput = asteriskHelper.getUserInput(playerNumber)
    while (lastUserInput == playerNumber or lastUserInput.isdigit() == False):
        asteriskHelper.playAudio("You can not pick yourself")
        lastUserInput = 12
        
    
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

#add all of the players here and wait for them to game to start
players = [Player(0, 1), Player(1, 2), Player(2, 3), Player(3, 4), Player(0, 5), Player(2, 6)]

#start game
    #introduce each player by giving him access to the 
#for player in players:
#    asteriskHelper.givePlayersRightToSpeak([player])
#    time.sleep(5000) #give them some time to introduce
    
#first round (makes not difference for the current roles, so just ignore it)

#start the normal game loop
while(isGameOver() == False):
    #night time
    asteriskHelper.playAudio("Everyone is falling a sleep")
    asteriskHelper.playAudio("The seears are waking up")
    
    allSeears = getListOfAllPlayersWithRole("seears")
    for seear in allSeears:
        result = asyncio.run(requestUserInput(seear.playerNumber))
        for player in players:
            if player.playerNumber == result:
                if(player.role == "wolves"):
                    asteriskHelper.playAudio("The person is a wolve")
                else:
                    asteriskHelper.playAudio("The person is not a wolve")
    


    allWolves = getListOfAllPlayersWithRole("wolves")
    asteriskHelper.connectPlayersPrivatly(allWolves)
    asteriskHelper.playAudio("Introduction to wolves voting system")
    wolvesVotingResult = asyncio.run(requestMulitibleUserInputs(allWolves))
    possibleVictim = getMostVoteResult(wolvesVotingResult)
    

    allWitches = getListOfAllPlayersWithRole("witch")
    asteriskHelper.connectPlayersPrivatly(allWitches)
    asteriskHelper.playAudio("Introduction to witches voting system") #maybe we can even tell them even the number of the victim 
    witchesVotingResult = asyncio.run(requestMulitibleUserInputs(allWitches))
    if(getMostVoteResult(witchesVotingResult) == 1):
        #how to kill
        asteriskHelper.playAudio("Introduce who to kill")
        seearsKillResult = requestMulitibleUserInputs(allWitches)
        for player in players:
            if player.playerNumber == getMostVoteResult(seearsKillResult):
                player.isAlive = False
                break
    elif(getMostVoteResult(witchesVotingResult) == 2):
        possibleVictim = -1
    
    #daytime
    asteriskHelper.connectPlayersPrivatly(players)
    if(possibleVictim == -1):
        asteriskHelper.playAudio("no one died")
    else:
        for player in players:
            if(player.number == possibleVictim):
                player.isAlive == False
        asteriskHelper.playAudio("someone passed away") # also maybe tell the number
    

    #village voting system 
    asteriskHelper.playAudio("Ask if they want to kill someone") #maybe we can even tell them even the number of the victim 
    villageVotingResult = asyncio.run(requestMulitibleUserInputs(getAllPlayersAlive()))
    if(getMostVoteResult(villageVotingResult) == 1):
        #how to kill
        asteriskHelper.playAudio("Introduce who to kill")
        villageKillResult = requestMulitibleUserInputs(getAllPlayersAlive())
        for player in players:
            if player.playerNumber == getMostVoteResult(villageKillResult):
                player.isAlive = False
                break

#game over
for player in players:
    asteriskHelper.kickPlayer(player.number)

#finished