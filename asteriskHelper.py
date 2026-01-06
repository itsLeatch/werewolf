
def playAudio(audioName, listOfPlayers):
    for player in listOfPlayers:
        print(f"Sending audio {audioName} to player {player.number}")
        try:
            if player.clientObject:
                player.clientObject.sendall(("m:" + audioName).encode())
        except (OSError, AttributeError, BrokenPipeError) as e:
            print(f"Error sending audio to player: {e}")
    print(f"Playing audio: {audioName} (not implemented)")

"""players can speak together privatly to find a good method"""
def connectPlayersPrivatly(listOfPlayers):
    print(f"Trying to connect players ${listOfPlayers}, but implement the function first")

"""all other players can listen but not talk """
def givePlayersRightToSpeak(listOfPlayers):
    print("implement right to speak")


"""Returns a number that was pushed on the panel"""
def getUserInput(player):
    print("implement the getUserInput")
    #return -1
    return input(f"Player {player}, enter your input: ")

def kickPlayer(player):
    print(f"Try to kick player {player}, but not implemented function!")