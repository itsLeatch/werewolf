import asyncio
import datetime
import anyio
import asyncari
from asyncari.state import ToplevelChannelState, DTMFHandler

from models import createPlayer, removePlayer

# --- Configuration ---
ARI_URL = "http://localhost:8088/"
ARI_USERNAME = "asterisk"
ARI_PASSWORD = "asterisk"
APP_NAME = "hello" # Must match the Stasis() app name in extensions.conf

clients = []
game_ready_event = asyncio.Event()  # Signals when 6 players have joined
PLAYERS_NEEDED = 3

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
    async def on_start(self):
        print(f"New user connected! Channel: {self.channel}")
        # Answer the call so it does not immediately hang up after entering Stasis
        await self.channel.answer()
        # Clear LANGUAGE so Asterisk does not look in language subfolders
        try:
            await client.channels.setChannelVar(
                channelId=self.channel.id,
                variable='LANGUAGE',
                value=''
            )
            print(f"LANGUAGE cleared for channel {self.channel.id}")
        except Exception as e:
            print(f"Failed clearing LANGUAGE for {self.channel.id}: {e}")
        await self.channel.play(media="sound:hello-world")
        player = Connection(self.channel)
        player.join_time = datetime.datetime.now()
        clients.append(player)
        createPlayer(self.channel.id)
        
        # Check if we now have enough players to start the game
        if len(clients) == PLAYERS_NEEDED:
            print(f"Reached {PLAYERS_NEEDED} players! Game will start soon.")
            game_ready_event.set()

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
            channel = event.channel
            if channel:
                print("New channel joining!")
                client.taskgroup.start_soon(HelloState(channel).start_task)

async def event_listener_end(client):
    """Listen for channel leaving Stasis and cleanup player state"""
    async with client.on_channel_event('StasisEnd') as listener:
        async for objs, event in listener:
            channel = event.channel
            if not channel:
                continue
            channel_id = channel.id
            print(f"Channel {channel_id} left Stasis. Cleaning up...")
            # Remove from local connection list
            global clients
            clients = [c for c in clients if c.id != channel_id]
            # Remove from global players list
            try:
                removePlayer(channel_id)
            except Exception as e:
                print(f"Failed to remove player {channel_id}: {e}")
        
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
        client.taskgroup.start_soon(event_listener_end, client)
        print("App starting soon!")
        print(f"Waiting for {PLAYERS_NEEDED} players to join...")

        # Import here to avoid circular imports
        from role import run_game
        
        # Run game loop manager and ARI listener concurrently
        async with anyio.create_task_group() as tg:
            tg.start_soon(run_ari_listener, client)
            tg.start_soon(playHoldMusicForWaitingPlayers, client)
            tg.start_soon(game_loop_manager, run_game, client)

async def run_ari_listener(client):
    """Run the ARI event listener loop"""
    async for event in client:
        print(f'Global event received: {event}')
        print("Use this event for anything central, that needs more than one channel!")

async def game_loop_manager(run_game, client):
    """Manages game instances - waits for players, starts game, repeats"""
    while True:
        # Wait for 6 players to join
        print(f"Waiting for {PLAYERS_NEEDED} players to join...")
        game_ready_event.clear()
        await game_ready_event.wait()
        
        print(f"{PLAYERS_NEEDED} players joined! Starting game...")
        await asyncio.sleep(1)  # Brief pause before starting
        
        # Run the game with the client
        await run_game(client)
        
        # Game finished - clear players and wait for next batch
        from models import players
        players.clear()
        clients.clear()
        print(f"Game finished! Waiting for next {PLAYERS_NEEDED} players...")

async def playHoldMusic(channel_id):
    """Play hold music on a specific channel in a loop"""
    try:
        while True:
            await playAudio("sound:hold_music", channel_id)
            await asyncio.sleep(30)  # Play for 30 seconds, then loop
    except Exception as e:
        print(f"Hold music stopped for {channel_id}: {e}")

async def playHoldMusicForWaitingPlayers(client):
    """Play hold music for all waiting players until game starts"""
    while len(clients) < PLAYERS_NEEDED and not game_ready_event.is_set():
        # Play hold music to all connected clients
        tasks = []
        for client_conn in clients:
            tasks.append(playAudio(client, "sound:hold_music", client_conn.id))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.sleep(2)  # Check every 2 seconds

"""get connection data"""
def getConnectionData(playerNumber):
    for client in clients:
        if client.id == playerNumber:
            return client
    return None

async def playAudio(client, audio_name, channel_id):
    """Play audio on a channel; uses keyword args to match asyncari signatures"""
    try:
        # Fetch channel object by ID; asyncari resources expect keyword arguments
        channel = await client.channels.get(channelId=channel_id)

        # Answer if not already up
        if channel.state == "Down":
            await channel.answer()

        await channel.play(media=audio_name)
    except Exception as e:
        print(f"Failed to play audio to {channel_id}: {e}")

"""players can speak together privatly to find a good method"""
async def connectPlayersPrivatly(client, listOfPlayers, nameOfBridge):
    print(f"Trying to connect players ${listOfPlayers}, but implement the function first")
    bridge = await client.bridges.create(
        type="mixing",
        name=nameOfBridge
    )
    for player in listOfPlayers:
        await client.bridges.addChannel(
            bridgeId=bridge.id,
            channel=player.number
        )
    return bridge.id

async def connectPlayersMuted(client, listOfPlayers, nameOfBridge):
    bridge = await client.bridges.create(
        type="mixing",
        name=nameOfBridge
    )
    for player in listOfPlayers:
        await client.bridges.addChannel(
            bridgeId=bridge.id,
            channel=player.number
        )
        await client.channels.mute(
            channelId=player.number,
            direction="in",
            mute=True
        )
    return bridge.id

"""a player is removed from the room they were in"""
async def removePlayerFromRoom(client, player, bridgeId):
    try:
        print("Removing channel!")
        await client.bridges.removeChannel(
            bridgeId=bridgeId,
            channel=player.number
        )
    except Exception:
        print("Channel already removed!")
        pass

async def removeRoom(client, bridgeId):
    try:
        print("Removing bridge!")
        await client.bridges.delete(bridgeId=bridgeId)
    except Exception:
        print("Bridge already removed!")
        pass

async def routePlayerToDifferentRoom(client, player, oldBridgeId, newBridgeId):
    await removePlayerFromRoom(client, player, oldBridgeId);
    await client.bridges.addChannel(
        bridgeId=newBridgeId,
        channel=player.number
    )


async def broadcastAudioToBridge(client, bridgeId, audio_name):
    """Play audio to all channels in a bridge"""
    try:
        bridge_channels = await client.bridges.get(bridgeId=bridgeId)
        for channel_id in bridge_channels.channels:
            await playAudio(client, audio_name, channel_id)
    except Exception as e:
        print(f"Failed to broadcast audio: {e}")
        

"""all other players can listen but not talk. one person speaks at a time.  """
async def givePlayersRightToSpeak(client, listOfPlayers, time=30):
    bridge = await connectPlayersPrivatly(client, listOfPlayers, "right_to_speak")
    for player in listOfPlayers:
        await client.channels.mute(
            channelId=player.number,
            direction="in",
            mute=True
        )
    for player in listOfPlayers:
        await allowSpeaker(client, player, time)
    for player in listOfPlayers:
        await removePlayerFromRoom(client, player, bridge.id)
    
async def allowSpeaker(client, player, time=30):
    await client.channels.mute(
        channelId=player.number,
        direction="in",
        mute=False
    )
    await asyncio.sleep(time)
    await client.channels.mute(
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
def kickPlayer(client, playerNumber):
    print(f"Try to kick player {playerNumber}, but not implemented function!")
    client.channels.hangup(channelId=playerNumber)





# DON'T EDIT BELOW THIS LINE
if __name__ == '__main__':
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        print('KeyboardInterrupt: shutting down')