import asyncio
import asteriskHelper
from models import (
    Player, players, createPlayer, getRoleCount, 
    getListOfAllAlivePlayersWithRole, isGameOver, getAllPlayersAlive
)

async def requestUserInput(playerNumber):
    """Request a single user input from a player"""
    lastUserInput = await asteriskHelper.getUserInput(playerNumber, 10)
    while (lastUserInput == playerNumber or (lastUserInput and not lastUserInput.isdigit())):
        await asteriskHelper.playAudio("You can not pick yourself", playerNumber)
        lastUserInput = await asteriskHelper.getUserInput(playerNumber, 10)
    return lastUserInput

async def requestMultipleUserInputs(listOfPlayers):
    """Request inputs from multiple players concurrently"""
    getUserInputs = []
    for player in listOfPlayers:
        getUserInputs.append(requestUserInput(player.number))
    results = await asyncio.gather(*getUserInputs)
    return results

def getMostVoteResult(results):
    """Return the most common vote result"""
    if not results:
        return None
    return max(set(results), key=results.count)

async def run_game():
    """Main game loop - runs concurrently with ARI listener"""
    # Players should already be added by the ARI connection handler
    # Just wait a moment for them to be ready
    await asyncio.sleep(1)
    
    print(f"Game starting with {len(players)} players")
    
    # Introduce each player
    for player in players:
        await asteriskHelper.givePlayersRightToSpeak([player])
        await asyncio.sleep(5)  # give them some time to introduce
    
    # Start the main game loop
    while not isGameOver():
        # Night time
        await asteriskHelper.playAudio("Everyone is falling asleep", None)
        await asteriskHelper.playAudio("The seers are waking up", None)
        
        # Seers vote
        allSeers = getListOfAllAlivePlayersWithRole("seer")
        for seer in allSeers:
            await asteriskHelper.playAudio(f"Seer please choose someone to see", seer.number)
            result = await requestUserInput(seer.number)
            for player in players:
                if result and player.number == int(result):
                    if player.role == "wolves":
                        await asteriskHelper.playAudio("The person is a wolf", seer.number)
                    else:
                        await asteriskHelper.playAudio("The person is not a wolf", seer.number)
        
        # Wolves vote
        allWolves = getListOfAllAlivePlayersWithRole("wolves")
        possibleVictim = None
        if allWolves:
            await asteriskHelper.connectPlayersPrivatly(allWolves, "wolves_bridge")
            await asteriskHelper.playAudio("Introduction to wolves voting system", None)
            wolvesVotingResult = await requestMultipleUserInputs(allWolves)
            possibleVictim = getMostVoteResult(wolvesVotingResult)

        # Witches vote
        allWitches = getListOfAllAlivePlayersWithRole("witch")
        if allWitches:
            await asteriskHelper.connectPlayersPrivatly(allWitches, "witches_bridge")
            await asteriskHelper.playAudio("Introduction to witches voting system", None)
            witchesVotingResult = await requestMultipleUserInputs(allWitches)
            if getMostVoteResult(witchesVotingResult) == "1":
                # Kill someone
                await asteriskHelper.playAudio("Introduce who to kill", None)
                witchKillResult = await requestMultipleUserInputs(allWitches)
                for player in players:
                    killTarget = getMostVoteResult(witchKillResult)
                    if killTarget and player.number == int(killTarget):
                        player.isAlive = False
                        break
            elif getMostVoteResult(witchesVotingResult) == "2":
                # Heal the possible victim
                possibleVictim = -1
        
        # Daytime
        await asteriskHelper.connectPlayersPrivatly(players, "day_bridge")
        if possibleVictim == -1:
            await asteriskHelper.playAudio("No one died", None)
        else:
            for player in players:
                if player.number == possibleVictim:
                    player.isAlive = False
            await asteriskHelper.playAudio("Someone passed away", None)
        await asteriskHelper.givePlayersRightToSpeak(getAllPlayersAlive())

        # Village voting system 
        await asteriskHelper.playAudio("Ask if they want to kill someone", None)
        villageVotingResult = await requestMultipleUserInputs(getAllPlayersAlive())
        if getMostVoteResult(villageVotingResult) == "1":
            # They decided to kill
            await asteriskHelper.playAudio("Introduce who to kill", None)
            villageKillResult = await requestMultipleUserInputs(getAllPlayersAlive())
            for player in players:
                killTarget = getMostVoteResult(villageKillResult)
                if killTarget and player.number == int(killTarget):
                    player.isAlive = False
                    break

    # Game over
    for player in players:
        asteriskHelper.kickPlayer(player.number)

    print("Game finished!")