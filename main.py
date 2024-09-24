import asyncio
import socket

from network.handlers.glob import register_all
from util.var import unpack_varint_socket, unpack_varint

from events.event_dispatcher import fire, PacketInEvent
from network.packet import PacketInRaw, PacketByteBuf


async def handle_connection(client: socket.socket):
    loop = asyncio.get_event_loop()

    try:
        while True:
            try:
                d = PacketByteBuf(await loop.sock_recv(client, 1024))
                packet_length = d.read_varint().value
                packet_id = d.read_varint().value
                packet_data = d.read_remaining()
            except asyncio.TimeoutError:
                print("Connection timed out")
                return
            except SystemExit:
                return

            await fire(PacketInEvent(client, PacketInRaw(packet_length, packet_id, packet_data)))

    finally:
        client.close()


async def run_server():
    await register_all()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 25577))
    server.listen(8)
    server.setblocking(True)
    # server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)

    loop = asyncio.get_event_loop()

    while True:
        client, _ = await loop.sock_accept(server)
        await loop.create_task(handle_connection(client))


asyncio.run(run_server())
