from server import Server, ServerSettings
from util.misc import _set_server, get_server

if __name__ == "__main__":
    server = Server(("127.0.0.1", 25565),
                    ServerSettings(
                        69,
                        {
                            "text": "A Gust server"
                        },
                        "1.20.4", 765
                    ))
    _set_server(server)

    get_server().run()
