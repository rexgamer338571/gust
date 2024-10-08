_server = None
_root_dir = ""


def _set_server(server) -> None:
    global _server
    _server = server


def get_server():
    return _server


def _set_root_dir(path: str):
    global _root_dir
    _root_dir = path


def get_root_dir() -> str:
    global _root_dir
    return _root_dir
