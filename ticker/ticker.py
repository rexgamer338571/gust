import socket
import time

from entity.player.player import Player
from network.handlers.play import PacketPlayOutKeepAlive

_tick = 0

players: list[Player] = []


async def tick():
    global _tick

    for player in players:
        if (_tick - player.last_keepalive) > 20 * 15:
            player.last_keepalive = _tick
            await PacketPlayOutKeepAlive().send(player)
            print("Sending keepalive", player.sock.getpeername())

    _tick += 1


async def start():
    while True:
        await tick()
        time.sleep(1 / 20)
