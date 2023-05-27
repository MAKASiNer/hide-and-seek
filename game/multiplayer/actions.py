from enum import IntEnum
from dataclasses import dataclass


class ActionID(IntEnum):
    PING = 0x1
    SHOW_CONTEXT = 0x2
    CALL = 0x3

    SET_LOBBY_STATUS = 0x10
    SET_READY = 0x11
    GET_READY = 0x12
    LEAVE_FROM_LOBBY = 0x13
    DUMP_GAME_MAP = 0x14
    LOAD_GAME_MAP = 0x15
    SET_GAME_LENGHT = 0x16

    START_GAME = 0x20
    FINISH_GAME = 0x21
    IN_GAME = 0x22
    CHECK_GAME = 0x23
    SET_POSITION = 0x24
    GET_POSITION = 0x25
    GET_ROLE = 0x26
    ATTACK = 0x27
    GET_WINNER = 0x28
    GET_GAME_TIMER = 0x29
    

@dataclass
class Action:
    action_id: ActionID = None
    data: object = None
    sender: tuple[str, int] = None