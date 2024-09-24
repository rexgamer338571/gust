entity_id = -1
teleport_id = -1


def next_entity_id() -> int:
    global entity_id
    entity_id += 1
    return entity_id


def next_teleport_id() -> int:
    global teleport_id
    teleport_id += 1
    return teleport_id
