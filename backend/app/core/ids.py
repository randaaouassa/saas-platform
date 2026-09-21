import uuid

from uuid6 import uuid7


def new_id() -> uuid.UUID:
    return uuid7()