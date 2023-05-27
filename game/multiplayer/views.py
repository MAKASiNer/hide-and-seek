import time
from random import choice
from dataclasses import asdict

from .models import *
from .actions import Action, ActionID
from .multiplayer import server


@server.default_action()
def default_action(action: Action, context: ServerContext):
    return 'ERROR: unknown action'


@server.bind_action(ActionID.PING)
@server.bind_action(ActionID.CALL)
def ping(action: Action, context: ServerContext):
    return 'OK'


@server.bind_action(ActionID.SHOW_CONTEXT)
def show_context(action: Action, context: ServerContext):
    return str(asdict(context))


@server.bind_action(ActionID.SET_LOBBY_STATUS)
def set_lobby_status(action: Action, context: ServerContext):
    context.lobby.status = action.data
    return 'OK'


@server.bind_action(ActionID.SET_READY)
def set_ready(action: Action, context: ServerContext):
    context.lobby.party[action.sender].ready = bool(action.data)
    return 'OK'


@server.bind_action(ActionID.GET_READY)
def get_ready(action: Action, context: ServerContext):
    if action.sender in context.lobby.party:
        return ('OK', context.lobby.party[action.sender].ready)
    return 'ERROR'


@server.bind_action(ActionID.LEAVE_FROM_LOBBY)
def leave_from_lobby(action: Action, context: ServerContext):
    context.kick(action.sender)
    return 'OK'


@server.bind_action(ActionID.START_GAME)
def start_game(action: Action, context: ServerContext):
    if any(map(lambda member: not member.ready, context.lobby.party.values())):
        return 'ERROR'
    else:
        for k in context.lobby.party:
            context.lobby.party[k].ready = False
    
    # задает статус игры и засекает время начала
    context.game.status = GAME_STATUS_GOING
    context.game.start_time = time.time()

    # переносит игроков из лобби в игру
    context.game.players = { member: PlayerData() for member in context.lobby.party }
    pl = choice(list(context.lobby.party.keys()))
    context.game.players[pl].set_role_as_hunter()

    # помещаем игроков в случайные места на карте
    maze_map = context.game.decrypted_maze_map()
    positions = list()
    for j in range(context.game.maze_height):
        for i in range(context.game.maze_width):
            if not maze_map[j][i]:
                positions.append((i + 0.5, j + 0.5))
    if positions:
        for k in context.game.players:
            context.game.players[k].position = choice(positions)

    return 'OK'


@server.bind_action(ActionID.FINISH_GAME)
def finish_game(action: Action, context: ServerContext):
    context.game.status = GAME_STATUS_BROKEN
    return 'OK'


@server.bind_action(ActionID.IN_GAME)
def in_game(action: Action, context: ServerContext):
    return 'Y' if action.sender in context.game.players else 'N'


@server.bind_action(ActionID.CHECK_GAME)
def check_game(action: Action, context: ServerContext):
    if context.game.status == GAME_STATUS_GOING:
        if not any(map(PlayerData.is_prey, context.game.players.values())):
            context.game.status = GAME_STATUS_FINISHED
            context.game.winner = PL_ROLE_HUNTER

        elif (time.time() - context.game.start_time > context.game.lenght or
              not any(map(PlayerData.is_hunter, context.game.players.values()))):
            context.game.status = GAME_STATUS_FINISHED
            context.game.winner = PL_ROLE_PREY

    return 'OK', context.game.status


@server.bind_action(ActionID.DUMP_GAME_MAP)
def dump_game_map(action: Action, context: ServerContext):
    context.game.maze_map = action.data
    return 'OK'


@server.bind_action(ActionID.LOAD_GAME_MAP)
def load_game_map(action: Action, context: ServerContext):
    return 'OK', context.game.maze_map


@server.bind_action(ActionID.SET_POSITION)
def set_position(action: Action, context: ServerContext):
    context.game.players[action.sender].position = action.data

    players = context.game.players.copy()
    players.pop(action.sender)

    # не призраки не могут видеть призраков
    if not context.game.players[action.sender].is_ghost():
        ghosts = filter(lambda k: players[k].is_ghost(), list(players.keys()))
        for ghost in ghosts:
            players.pop(ghost)

    return 'OK', list(map(asdict, players.values()))


@server.bind_action(ActionID.GET_POSITION)
def get_position(action: Action, context: ServerContext):
    if action.sender in context.game.players:
        return ('OK', context.game.players[action.sender].position)
    return 'ERROR'


@server.bind_action(ActionID.GET_ROLE)
def get_role(action: Action, context: ServerContext):
    if action.sender in context.game.players:
        return ('OK', context.game.players[action.sender].role)
    return 'ERROR'


@server.bind_action(ActionID.ATTACK)
def attack(action: Action, context: ServerContext):
    a = context.game.players[action.sender].position
    for player in context.game.players:
        if player == action.sender:
            continue
        # если расстояние между охотником и жертвой достаточное
        b = context.game.players[player].position
        if (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 < 0.6 ** 2:
            # жертва погибает
            context.game.players[player].set_role_as_ghost()
            return 'OK'
        
    return 'ERROR'

@server.bind_action(ActionID.GET_WINNER)
def get_winner(action: Action, context: ServerContext):
    return 'OK', context.game.winner


@server.bind_action(ActionID.GET_GAME_TIMER)
def get_game_timer(action: Action, context: ServerContext):
    if context.game.status != GAME_STATUS_GOING:
        return 'ERROR'
    return 'OK', context.game.start_time + context.game.lenght - time.time()


@server.bind_action(ActionID.SET_GAME_LENGHT)
def set_game_lenght(action: Action, context: ServerContext):
    context.game.lenght = float(action.data)
    return 'OK'