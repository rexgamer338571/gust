import socket
import time

from entity.player.player import Player

_tick = 0
_last_keepalive = 0

players: list[Player] = []


def tick():
    global _tick, _last_keepalive

    if (_tick - _last_keepalive) > 20 * 15:
        _last_keepalive = _tick

    _tick += 1


def start():
    while True:
        tick()
        time.sleep(1 / 20)
