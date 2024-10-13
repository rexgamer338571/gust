import os

from server import Server, ServerSettings
from util.misc import _set_server, get_server, _set_root_dir

if __name__ == "__main__":
    _set_root_dir(os.getcwd())

    server = Server(("127.0.0.1", 25566),
                    ServerSettings(
                        69,
                        {
                            "text": "A Gust server"
                        },
                        "1.20.4", 765
                    ))
    _set_server(server)

    get_server().run()
