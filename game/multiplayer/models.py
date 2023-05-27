import bitarray
from dataclasses import dataclass, field


PL_ROLE_PREY = 'prey'
PL_ROLE_HUNTER = 'hunter'
PL_ROLE_GHOST = 'ghost'

LOBBY_STATUS_OPENED = 'open'
LOBBY_STATUS_CLOSED = 'closed'

GAME_STATUS_FINISHED = 'finished'
GAME_STATUS_GOING = 'going'
GAME_STATUS_BROKEN = 'broken'


Address = tuple[str, int]


@dataclass
class MemberData:
    lastcall: float = 0
    ready: bool = False


@dataclass
class Lobby:
    status: str = 'close'
    party: dict[Address, MemberData] = field(default_factory=dict)


@dataclass
class PlayerData:
    position: tuple[float, float] = (0, 0)
    role: str = 'prey'

    def set_role_as_hunter(self):
        self.role = 'hunter'

    def is_hunter(self):
        return self.role == 'hunter'
    
    def set_role_as_prey(self):
        self.role = 'prey'

    def is_prey(self):
        return self.role == 'prey'
    
    def set_role_as_ghost(self):
        self.role = 'ghost'
    
    def is_ghost(self):
        return self.role == 'ghost'


@dataclass
class Game:
    

    status: str = 'end'
    start_time: float = 0
    lenght: float = 2 * 60 # 2 минуты
    winner: str = None
    maze_map: tuple[int, int, int] = (0, 0, 0)
    players: dict[Address, PlayerData] = field(default_factory=dict)


    @staticmethod
    def encrypt_maze_map(list2d) -> tuple[int, int, int]:
        h, w = len(list2d), len(list2d[0])
        data = bitarray.bitarray() 
        for j in range(h):
            for i in range(w):
                data.append(list2d[j][i])
        compr_data = int.from_bytes(data.tobytes(), byteorder='big')
        return w, h, compr_data
    

    def encrypted_maze_map(self) -> tuple[int, int, int]:
        return self.maze_map


    @staticmethod
    def decrypt_maze_map(w, h, crt_data) -> list[list[bool]]:
        data = bitarray.bitarray()
        data.frombytes(crt_data.to_bytes((w * h + 7) // 8, byteorder='big'))
        map = [[False for _ in range(w)] for _ in range(h)]
        for j in range(h):
            for i in range(w):
                map[j][i] = bool(data[i + j * w])
        return map
    
    
    def decrypted_maze_map(self) -> list[list[bool]]:
        return self.decrypt_maze_map(*self.maze_map)
    
    @property
    def maze_width(self):
        return self.maze_map[0]
    
    @property
    def maze_height(self):
        return self.maze_map[1]



@dataclass 
class ServerContext:
    lobby: Lobby = Lobby()
    game: Game = Game()

    def kick(self, member):
        if member in self.lobby.party:
            self.lobby.party.pop(member)
        if member in self.game.players:
            self.game.players.pop(member)