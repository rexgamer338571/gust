HANDSHAKE = 0
STATUS = 1
LOGIN = 2
CONFIGURATION = 3
PLAY = 4


current_state = 0


def set_state(new_state: int):
    global current_state
    current_state = new_state


def get_state() -> int:
    return current_state


handshake_array = [None for i in range(256)]
status_array = [None for l in range(256)]
login_array = [None for j in range(256)]
configuration_array = [None for k in range(256)]
play_array = [None for m in range(256)]

states = [
    handshake_array,
    status_array,
    login_array,
    configuration_array,
    play_array
]
