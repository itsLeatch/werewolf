import datetime
import anyio
import asyncari
from asyncari.state import ToplevelChannelState, DTMFHandler

# --- Configuration ---
ARI_URL = "http://localhost:8088/"
ARI_USERNAME = "asterisk"
ARI_PASSWORD = "asterisk"
APP_NAME = "hello" # Must match the Stasis() app name in extensions.conf

clients = []

class Connection:
    def __init__(self, channel):
        self.channel = channel
        self.id = channel.id
        self.vote = None
        self.bridge_id = None
        self.is_muted = False
        self.is_connected = True
        self.join_time = None
        self.data = {}

class HelloState(ToplevelChannelState, DTMFHandler):

    # Runs on every new connection
    async def on_start(self, channel):
        print(f"New user connected! Channel: {self.channel_id}")
        await self.channel.play(media="sound:hello-world")
        player = Connection(channel)
        player.join_time = datetime.now()
        clients.append(player)

    async def on_dtmf(self, event):
        print(f"Digit {event.digit} pressed on channel {self.channel_id}")
        player = next((p for p in clients if p.id == self.channel_id), None)
        if not player:
            return
        player.vote = event.digit

async def event_listener(client):
    """The task that listens to events as long as the code runs"""
    async with client.on_channel_event('StasisStart') as listener:
        async for objs, event in listener:
            channel = objs.get('channel')
            if channel:
                print("New channel joining!")
                client.taskgroup.start_soon(HelloState(channel).start_task)
        
async def main():
    """Runs the main event loop"""

    async with asyncari.connect(
        base_url=ARI_URL,
        apps=APP_NAME,
        username=ARI_USERNAME,
        password=ARI_PASSWORD
    ) as client:
        client.taskgroup.start_soon(event_listener, client)
        print("App starting soon!")

        async for event in client:
            print(f'Global event received: {event}')
            print("Use this event for anything central, that needs more than one channel!")


def playAudio(audioName):
    #print("Trying to play an audio, but it is not working, because the function was not implemented yet")
    print(f"Playing audio: {audioName} (not really, implement the function first)")

"""players can speak together privatly to find a good method"""
def connectPlayersPrivatly(listOfPlayers):
    print(f"Trying to connect players ${listOfPlayers}, but implement the function first")

"""all other players can listen but not talk """
def givePlayersRightToSpeak(listOfPlayers):
    print("implement right to speak")


"""Returns a number that was pushed on the panel"""
def getUserInput(playerNumber):
    print("implement the getUserInput")
    #return -1
    return input(f"Player {playerNumber}, enter your input: ")

def kickPlayer(playerNumber):
    print(f"Try to kick player {playerNumber}, but not implemented function!")






if __name__ == '__main__':
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        print('KeyboardInterrupt: shutting down')