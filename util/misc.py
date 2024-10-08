_server = None


def _set_server(server) -> None:
    global _server
    _server = server


def get_server():
    return _server
