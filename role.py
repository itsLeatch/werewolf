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
    # Assign game player numbers
    from models import assignGamePlayerNumbers
    assignGamePlayerNumbers()
    
    welcomeBridge = await asteriskHelper.connectPlayersPrivatly(players, "introduction_bridge")
    # Introduce each player
    for player in players:
        await asteriskHelper.playAudio("sound:audio/you_are_the", player.number)
        if player.role == "wolves":
            await asteriskHelper.playAudio("sound:audio/werewolf", player.number)
        elif player.role == "seer":
            await asteriskHelper.playAudio("sound:audio/seer", player.number)
        elif player.role == "villager":
            await asteriskHelper.playAudio("sound:audio/villager", player.number)
        elif player.role == "witch":
            await asteriskHelper.playAudio("sound:audio/witch", player.number)
        await asteriskHelper.allowSpeaker(player, 15)  # give them some time to introduce
        await asyncio.sleep(5)  # give them some time to introduce
    
    await asteriskHelper.removeRoom(welcomeBridge.id)
    # Start the main game loop
    while not isGameOver():
        # Night time
        # await asteriskHelper.playAudio("Everyone is falling asleep", None)
        # await asteriskHelper.playAudio("The seers are waking up", None)
        
        # Seers vote
        allSeers = getListOfAllAlivePlayersWithRole("seer")
        for seer in allSeers:
            await asteriskHelper.playAudio("sound:audio/If_you_would_like_to_see_a_player's_card,_press_1._If_you_would_like_to_continue,_press_2", seer.number)
            result = await requestUserInput(seer.number)
            if result == "1":
                # await asteriskHelper.playAudio("Introduce who to see", seer.number)
                result = await requestUserInput(seer.number)
                for player in players:
                    if result and player.gamePlayerNum == int(result):
                        await asteriskHelper.playAudio(f"Player_{player.gamePlayerNum}", seer.number)
                        await asteriskHelper.playAudio("sound:audio/is_the", seer.number)
                        for player in players:
                            if player.role == "wolves":
                                await asteriskHelper.playAudio("sound:audio/werewolf", seer.number)
                            elif player.role == "seer":
                                await asteriskHelper.playAudio("sound:audio/seer", seer.number)
                            elif player.role == "villager":
                                await asteriskHelper.playAudio("sound:audio/villager", seer.number)
                            elif player.role == "witch":
                                await asteriskHelper.playAudio("sound:audio/witch", seer.number)
        
        # Wolves vote
        allWolves = getListOfAllAlivePlayersWithRole("wolves")
        possibleVictim = None
        if allWolves:
            bridge = await asteriskHelper.connectPlayersPrivatly(allWolves, "wolves_bridge")
            await asteriskHelper.broadcastAudioToBridge(bridge.id, "sound:audio/Press_the_player_of_the_number_you_would_like_to_kill")
            wolvesVotingResult = await requestMultipleUserInputs(allWolves)
            possibleVictim = getMostVoteResult(wolvesVotingResult)

        # Witches vote
        allWitches = getListOfAllAlivePlayersWithRole("witch")
        if allWitches:
            bridge = await asteriskHelper.connectPlayersPrivatly(allWitches, "witches_bridge")
            await asteriskHelper.broadcastAudioToBridge(bridge.id, "sound:audio/If_you_would_like_to_kill_a_player,_press_one")
            await asteriskHelper.broadcastAudioToBridge(bridge.id, "sound:audio/If_you_would_like_to_revive_the_player,_press_two")
            witchesVotingResult = await requestMultipleUserInputs(allWitches)
            if getMostVoteResult(witchesVotingResult) == "1":
                # Kill someone
                await asteriskHelper.broadcastAudioToBridge(bridge.id, "sound:audio/Press_the_player_of_the_number_you_would_like_to_kill")
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
        bridge = await asteriskHelper.connectPlayersPrivatly(players, "day_bridge")
        if possibleVictim == -1:
            await asteriskHelper.broadcastAudioToBridge(bridge.id, "sound:audio/No_one")
            await asteriskHelper.broadcastAudioToBridge(bridge.id, "sound:audio/Has_been_eliminated")
        else:
            for player in players:
                if player.number == possibleVictim:
                    player.isAlive = False
                    await asteriskHelper.broadcastAudioToBridge(bridge.id, f"sound:audio/Player_{player.gamePlayerNum}")
                    await asteriskHelper.broadcastAudioToBridge(bridge.id, "sound:audio/Has_been_eliminated")
                    await asteriskHelper.kickPlayer(player.number)
                    break
        await asteriskHelper.givePlayersRightToSpeak(getAllPlayersAlive())

        # Village voting system 
        await asteriskHelper.broadcastAudioToBridge(bridge.id, "sound:audio/If_you_would_like_to_kill_a_player,_press_one")
        villageVotingResult = await requestMultipleUserInputs(getAllPlayersAlive())
        if getMostVoteResult(villageVotingResult) == "1":
            # They decided to kill
            await asteriskHelper.broadcastAudioToBridge(bridge.id, "sound:audio/Press_the_player_of_the_number_you_would_like_to_kill")
            villageKillResult = await requestMultipleUserInputs(getAllPlayersAlive())
            for player in players:
                killTarget = getMostVoteResult(villageKillResult)
                if killTarget and player.number == int(killTarget):
                    player.isAlive = False
                    await asteriskHelper.broadcastAudioToBridge(bridge.id, f"sound:audio/Player_{player.gamePlayerNum}")
                    await asteriskHelper.broadcastAudioToBridge(bridge.id, "sound:audio/Has_been_eliminated")
                    await asteriskHelper.kickPlayer(player.number)
                    break

    # Game over
    for player in players:
        await asteriskHelper.kickPlayer(player.number)

    print("Game finished!")