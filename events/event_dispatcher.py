import socket
from typing import Any

from entity.player.player import Player
from network.packet import PacketInRaw
from util.state import states, get_state


class Event:
    handlers: dict[type, list] = {}


class PlayerEvent(Event):
    def __init__(self, client: Player):
        self.client: Player = client


class HandlersModifiedEvent(Event):
    def __init__(self, e: type[Event], c):
        super().__init__()
        self.target = e
        self.handler = c


class PacketInEvent(PlayerEvent):
    def __init__(self, c: Player, p: PacketInRaw):
        super().__init__(c)
        self.packet = p

    async def call_packet_listener(self):
        await states[get_state()][self.packet.packet_id](self.client, self.packet)


class TeleportConfirmEvent(PlayerEvent):
    def __init__(self, l: Player, teleport_id: int):
        super().__init__(l)
        self.teleport_id = teleport_id


async def register(e: type[Event], c):
    if e in Event.handlers.items():
        Event.handlers[e].append(c)
    else:
        Event.handlers[e] = [c]

    await fire(HandlersModifiedEvent(e, c))


def register_packet(state: int, id_: int, f):
    states[state][id_] = f


async def fire0(e: Event):
    for handler in Event.handlers[type(e)]:
        await handler(e)


async def fire(e: Event):
    t = type(e)

    for i in Event.handlers.items():
        if i[0] == t:
            await fire0(e)

