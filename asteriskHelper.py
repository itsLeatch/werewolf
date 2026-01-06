import asyncio
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
app = None

class Connection:
    def __init__(self, channel):
        self.channel = channel
        self.id = channel.id
        self.vote = None
        self.vote_time = None
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
        player.join_time = datetime.datetime.now()
        clients.append(player)

    async def on_dtmf(self, event):
        print(f"Digit {event.digit} pressed on channel {self.channel_id}")
        player = next((p for p in clients if p.id == self.channel_id), None)
        if not player:
            return
        player.vote = event.digit
        player.vote_time = datetime.datetime.now()

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
    global client

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


async def playAudio(audioName, channelId):
    print(f"Playing audio: {audioName} (not implemented)")
    await client.channels.play(channel=channelId, media=audioName)

"""players can speak together privatly to find a good method"""
async def connectPlayersPrivatly(listOfPlayers, nameOfBridge):
    print(f"Trying to connect players ${listOfPlayers}, but implement the function first")
    bridge = await app.bridges.create(
        type="mixing",
        name=nameOfBridge
    )
    for player in listOfPlayers:
        await app.bridges.addChannel(
            bridgeId=bridge.id,
            channelId=player.number
        )
    return bridge.id

"""a player is removed from the room they were in"""
async def removePlayerFromRoom(player, bridgeId):
    try:
        print("Removing channel!")
        await app.bridges.removeChannel(
            bridgeId=bridgeId,
            channelId=player.number
        )
    except Exception:
        print("Channel already removed!")
        pass

async def routePlayerToDifferentRoom(player, oldBridgeId, newBridgeId):
    await removePlayerFromRoom(player, oldBridgeId);
    await app.bridges.addChannel(
        bridgeId=newBridgeId,
        channelId=player.number
    )


"""all other players can listen but not talk. one person speaks at a time.  """
async def givePlayersRightToSpeak(listOfPlayers, time=30):
    bridge = await connectPlayersPrivatly(listOfPlayers, "right_to_speak")
    for player in listOfPlayers:
        await app.channels.mute(
            channelId=player.number,
            direction="in",
            mute=True
        )
    for player in listOfPlayers:
        await allowSpeaker(player, time)
    for player in listOfPlayers:
        await removePlayerFromRoom(player, bridge.id)
    
async def allowSpeaker(player, time=30):
    await app.channels.mute(
        channelId=player.number,
        direction="in",
        mute=False
    )
    await asyncio.sleep(time)
    await app.channels.mute(
        channelId=player.number,
        direction="in",
        mute=True
    )


"""Returns a number that was pushed on the panel"""
async def getUserInput(player, timeout=15):
    print("Awaiting user input...")
    await asyncio.sleep(timeout)
    if player.vote:
        if (datetime.datetime.now() - player.vote_time).total_seconds() <= timeout:
            return player.vote
    return None

"""Hang up"""
def kickPlayer(playerNumber):
    print(f"Try to kick player {playerNumber}, but not implemented function!")
    app.channels.hangup(channelId=playerNumber)





# DON'T EDIT BELOW THIS LINE
if __name__ == '__main__':
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        print('KeyboardInterrupt: shutting down')